"""Prepare an immutable release. Never activate or replace existing data by default."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4
from provenance import atomic_json, now, inputs
from release import activate, validate_snapshot
from registry import sha256

def stage_release(root, province_data='data/province-modis.csv', build=True):
    from update_forecasts import run
    from snapshot import build_snapshot
    release_id=now().replace(':','-')+'-'+uuid4().hex[:8]
    stage=Path(root)/release_id
    stage.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter()
    sources={'uni':'data/modis.csv','multi':'data/modis-multi.csv','common':'data/modis-multi.csv','province':str(province_data)}
    try:
        for mode,source in sources.items():
            run(mode,source,stage/f'latest-{mode}.csv')
        snapshot=build_snapshot(stage,province_data,dict(id=release_id,created_at=now(),status='candidate'))
        count=validate_snapshot(snapshot)
        atomic_json(stage/'snapshot.json',snapshot)
        if build:
            npm=shutil.which('npm.cmd' if os.name=='nt' else 'npm')
            if npm is None: raise RuntimeError('Atlas derlemesi için Node.js/npm gerekli')
            if not Path('web/node_modules').is_dir():
                subprocess.run([npm,'ci'],cwd='web',check=True)
            env={**os.environ,'LST_SNAPSHOT':str((stage/'snapshot.json').resolve()),'VITE_OFFLINE':'true'}
            subprocess.run([npm,'run','build','--','--outDir',str((stage/'web').resolve())],cwd='web',env=env,check=True)
            shutil.copy2(stage/'web/index.html',stage/'Atlas.html')
        atomic_json(stage/'manifest.json',dict(release_id=release_id,status='prepared',created_at=now(),
            inputs=inputs(sources.values()),snapshot_sha256=sha256(stage/'snapshot.json'),
            offline_html_sha256=sha256(stage/'Atlas.html') if build else None,
            pipeline_files=inputs(sorted(Path('scripts').glob('*.py'))+sorted(Path('web/src').glob('*.tsx'))+
                ['web/src/style.css','web/vite.config.ts','web/package.json','web/package-lock.json']),
            forecasts=count,seconds=time.perf_counter()-started,offline_built=build))
    except Exception as exc:
        atomic_json(stage/'failure.json',dict(status='failed',error_type=type(exc).__name__,time=now()))
        raise
    return stage

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=Path('releases'))
    p.add_argument('--province-data',type=Path,default=Path('data/province-modis.csv'))
    p.add_argument('--no-build',action='store_true')
    p.add_argument('--activate',type=Path,help='Önceden incelenmiş yayın klasörü; ayrı açık işlem')
    p.add_argument('--publish',action='store_true',help='Sadece --activate ile veritabanını etkinleştirir')
    a=p.parse_args()
    if a.publish and a.activate is None: p.error('--publish için --activate gerekli')
    if a.activate:
        from publish import publish_snapshot
        print(activate(a.activate,root=a.root,publish_db=publish_snapshot if a.publish else None))
    else:
        print(stage_release(a.root,a.province_data,not a.no_build))
if __name__=='__main__':main()
