"""Append-only releases and a transactional active pointer. No legacy rows deleted."""
import argparse
import json
import os
from pathlib import Path
import psycopg
from release import validate_snapshot

def publish_snapshot(snapshot, *, connection=None, initialize=False, seed_only=False, allow_coverage_drop=False):
    validate_snapshot(snapshot)
    release_id=snapshot['release']['id']
    with psycopg.connect(connection if connection is not None else os.environ.get('DATABASE_URL','')) as db:
        if initialize:
            db.execute(Path('sql/init.sql').read_text(encoding='utf8'))
        # Serialize publishers. A failure rolls back inserts and activation together.
        db.execute('SELECT pg_advisory_xact_lock(73682119)')
        active=db.execute('SELECT release_id FROM lst_active_release WHERE singleton=true').fetchone()
        if seed_only and active:
            return active[0]
        if active and not allow_coverage_drop:
            previous=db.execute("SELECT name,jsonb_array_length(COALESCE(result->'runs','[]'::jsonb)) FROM lst_release_province WHERE release_id=%s",(active[0],)).fetchall()
            dropped=[city for city,count in previous if len(snapshot['regions'].get(city,{}).get('runs',[]))<count]
            if dropped:raise ValueError('Tahmin kapsamı azaldı; açık inceleme gerekli: '+', '.join(dropped))
        existing=db.execute('SELECT metadata FROM lst_release WHERE id=%s',(release_id,)).fetchone()
        if existing:
            raise ValueError('Yayın kimliği zaten kayıtlı; geçmiş yayın değiştirilmez')
        db.execute('INSERT INTO lst_release(id,metadata) VALUES(%s,%s::jsonb)',(release_id,json.dumps(snapshot['release'])))
        for feature in snapshot['features']:
            city=feature['properties']['name']
            db.execute('''INSERT INTO lst_release_province(release_id,name,geom,result)
                VALUES(%s,%s,ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)),%s::jsonb)''',
                (release_id,city,json.dumps(feature['geometry']),json.dumps(snapshot['regions'][city],allow_nan=False)))
        count=db.execute('SELECT count(*) FROM lst_release_province WHERE release_id=%s',(release_id,)).fetchone()[0]
        if count!=81:raise ValueError('Yayın il sayısı 81 değil')
        db.execute('''INSERT INTO lst_active_release(singleton,release_id) VALUES(true,%s)
            ON CONFLICT(singleton) DO UPDATE SET release_id=excluded.release_id''',(release_id,))
    return release_id

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True)
    p.add_argument('--initialize',action='store_true',help='Şema oluşturur; mevcut DB için önce onay alın')
    p.add_argument('--seed-only',action='store_true',help='Etkin yayın varsa dokunma')
    p.add_argument('--allow-coverage-drop',action='store_true',help='Yalnızca kullanıcı kapsam azalmasını onayladıktan sonra')
    a=p.parse_args()
    print(publish_snapshot(json.loads(a.snapshot.read_text(encoding='utf8')),initialize=a.initialize,seed_only=a.seed_only,allow_coverage_drop=a.allow_coverage_drop))
