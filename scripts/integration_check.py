"""Isolated PostgreSQL/PostGIS + API + optional browser acceptance tests.

Creates a temporary cluster; never connects to a user's existing database.
"""
from pathlib import Path
import argparse
import copy
import getpass
import json
import os
import signal
import subprocess
import tempfile
import time
import psycopg
from publish import publish_snapshot
from test_api import call,check
from provenance import atomic_json,now

def wait_for(fn,timeout=40):
    until=time.monotonic()+timeout
    while True:
        try:
            if fn():return
        except Exception:pass
        if time.monotonic()>until:raise RuntimeError('Test servisi zamanında başlamadı')
        time.sleep(.25)

def run(pg_bin,dotnet,snapshot,browser=False):
    root=Path.cwd();pg_bin=Path(pg_bin).resolve();dotnet=str(Path(dotnet).resolve())
    value=json.loads(Path(snapshot).read_text(encoding='utf8'))
    with tempfile.TemporaryDirectory(prefix='lst-integration-') as directory:
        folder=Path(directory);cluster=folder/'pg';log=(folder/'services.log').open('w')
        env=os.environ.copy();role=getpass.getuser()
        env['LD_LIBRARY_PATH']=str(pg_bin.parents[3]/'lib/x86_64-linux-gnu')+':'+env.get('LD_LIBRARY_PATH','')
        subprocess.run([str(pg_bin/'initdb'),'-D',str(cluster),'-U',role,'--auth=trust','--encoding=UTF8','--no-locale'],check=True,env=env,stdout=log,stderr=log)
        dsn=f'host=127.0.0.1 port=55432 dbname=postgres user={role}'
        def start():return subprocess.Popen([str(pg_bin/'postgres'),'-D',str(cluster),'-k','','-h','127.0.0.1','-p','55432'],env=env,stdout=log,stderr=log)
        def ready():
            with psycopg.connect(dsn,connect_timeout=1) as db:return db.execute('SELECT 1').fetchone()[0]==1
        pg=start();api=None
        try:
            wait_for(ready)
            publish_snapshot(value,connection=dsn,initialize=True)
            with psycopg.connect(dsn) as db:
                before=db.execute('SELECT release_id FROM lst_active_release').fetchone()[0]
            invalid=copy.deepcopy(value);invalid['release']['id']='test-rollback-only';invalid['features'][0]['geometry']={'type':'Invalid'}
            try:publish_snapshot(invalid,connection=dsn)
            except psycopg.Error:pass
            else:raise AssertionError('Expected transactional failure')
            with psycopg.connect(dsn) as db:
                assert db.execute('SELECT release_id FROM lst_active_release').fetchone()[0]==before
                assert db.execute('SELECT count(*) FROM lst_release WHERE id=%s',('test-rollback-only',)).fetchone()[0]==0
            env['ConnectionStrings__Lst']=f'Host=127.0.0.1;Port=55432;Database=postgres;Username={role}'
            env['ASPNETCORE_URLS']='http://127.0.0.1:5274'
            api=subprocess.Popen([dotnet,'run','--project','api','--no-launch-profile','--no-build'],env=env,stdout=log,stderr=log)
            base='http://127.0.0.1:5274';wait_for(lambda:call(base,'/health')[0]==200)
            atomic_json(root/'results/verification/api-integration.json',check(base))
            from urllib.parse import quote
            import math
            layer=call(base,'/api/tahmin-katmani?release='+quote(before,safe=''))[2]
            key=lambda r:(r['city'],r['mode'],r['model'],r['h'],r['date'],r['origin'])
            expected={key(r):r['prediction'] for region in value['regions'].values() for r in region.get('runs',[]) if r['mode']=='province' and r['publishable']}
            assert len(layer)==len(expected)
            assert all(math.isclose(r['prediction'],expected[key(r)],abs_tol=1e-12) for r in layer)
            reduced=copy.deepcopy(value);reduced['release']['id']='test-coverage-rejection'
            reduced['regions']['Antalya']['runs']=[]
            try:publish_snapshot(reduced,connection=dsn)
            except ValueError:pass
            else:raise AssertionError('Coverage decrease was accepted')
            if browser:subprocess.run(['npm','exec','playwright','test'],cwd=root/'web',env=env,check=True)
            pg.send_signal(signal.SIGINT);pg.wait(timeout=10)
            assert call(base,'/health')[0]==503
            pg=start();wait_for(ready);wait_for(lambda:call(base,'/health')[0]==200)
            assert call(base,'/api/iller')[0]==200
            with psycopg.connect(dsn) as db:
                assert db.execute('SELECT count(*) FROM lst_release_province').fetchone()[0]==81
            atomic_json(root/'results/verification/system-integration.json',dict(status='passed',time=now(),
                database='isolated temporary PostgreSQL/PostGIS',http_contract_checks=10,rollback=True,
                database_outage_503=True,reconnect=True,restart_preserves_rows=True,coverage_drop_rejected=True,
                snapshot_api_forecasts_equal=True,browser=browser,release_id=before))
        finally:
            if api is not None:api.terminate();api.wait(timeout=10)
            if pg.poll() is None:pg.send_signal(signal.SIGINT);pg.wait(timeout=10)
            log.close()
            (root/'results/verification/system-services.txt').write_bytes((folder/'services.log').read_bytes())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pg-bin',required=True);p.add_argument('--dotnet',required=True);p.add_argument('--snapshot',required=True);p.add_argument('--browser',action='store_true');a=p.parse_args();run(a.pg_bin,a.dotnet,a.snapshot,a.browser)
