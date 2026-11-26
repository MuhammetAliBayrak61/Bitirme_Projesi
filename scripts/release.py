"""Immutable snapshots. DB activation is canonical for API; offline has its own pointer."""
from pathlib import Path
import json
import re
from datetime import date,timedelta
from provenance import atomic_json
from registry import sha256

def validate_snapshot(snapshot, expected_cities=81):
    names=[f['properties']['name'] for f in snapshot['features']]
    if len(names)!=expected_cities or len(set(names))!=expected_cities or set(names)!=set(snapshot['regions']):
        raise ValueError('Beklenen il sayısı/kapsamı uyuşmuyor; yayın reddedildi')
    release=snapshot.get('release',{})
    if not release.get('id') or not release.get('created_at'):
        raise ValueError('Yayın kimliği veya zamanı eksik')
    count=0
    for city,region in snapshot['regions'].items():
        keys=set()
        for run in region.get('runs',[]):
            key=tuple(run[k] for k in ('mode','model','origin','date','h'))
            if key in keys or run['city']!=city:
                raise ValueError('Tekrarlanan/yanlış il tahmini')
            keys.add(key)
            if not re.fullmatch('[a-f0-9]{64}',run.get('version','')) or not re.fullmatch('[a-f0-9]{64}',run.get('data_version','')):
                raise ValueError('Tahminde veri/model sürümü eksik')
            if run['date']<=run['origin'] or run['h'] not in (1,2,3,4):
                raise ValueError('Geçersiz tahmin hedefi')
            origin=date.fromisoformat(run['origin'])
            doy=(origin-date(origin.year,1,1)).days
            if doy%8 or doy>360:raise ValueError('Geçersiz MODIS başlangıcı')
            target=origin
            for _ in range(run['h']):
                target=date(target.year+1,1,1) if (target-date(target.year,1,1)).days==360 else target+timedelta(days=8)
            if target.isoformat()!=run['date']:raise ValueError('Tahmin ufku ve hedef tarih uyuşmuyor')
            if run.get('publishable') and not (-50<=run['prediction']<=85 and run['recent_n']>=4 and run['n']>=12):
                raise ValueError('Yayın kalite eşiği sağlanmıyor')
            count+=1
    if count==0:
        raise ValueError('Tahminsiz yayın reddedildi')
    return count

def activate(stage, *, root=Path('releases'), publish_db=None):
    stage=Path(stage)
    path=stage/'snapshot.json'
    snapshot=json.loads(path.read_text(encoding='utf8'))
    validate_snapshot(snapshot)
    manifest=json.loads((stage/'manifest.json').read_text(encoding='utf8'))
    if manifest['snapshot_sha256']!=sha256(path):
        raise ValueError('Hazırlanan snapshot değişmiş')
    if publish_db is not None:
        # No file pointer is changed in DB mode. API reads one transactional active ID.
        publish_db(snapshot)
    else:
        if not (stage/'Atlas.html').is_file():
            raise ValueError('Çevrimdışı yayın için derlenmiş Atlas.html gerekli')
        if manifest.get('offline_html_sha256')!=sha256(stage/'Atlas.html'):
            raise ValueError('Çevrimdışı HTML bütünlüğü doğrulanamadı; aday yayını yeniden hazırlayın')
        atomic_json(root/'current.json',dict(release_id=snapshot['release']['id'],path=str(stage.resolve()),snapshot_sha256=sha256(path)))
    return snapshot['release']['id']
