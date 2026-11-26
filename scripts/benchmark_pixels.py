"""Real MODIS pixels from distinct Terra scenes. No synthetic row multiplication."""
from pathlib import Path
import argparse
import json
from urllib.request import urlopen
import numpy as np
import pandas as pd
from rasterio.io import MemoryFile
from province_archive import PC,FEATURES,read,zones,blob_inventory,qc_mask
from provenance import atomic_json,now
from registry import sha256

def extract(output,year=2026,dates=3):
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    token=json.loads(read(PC+'/sas/v1/token/modiseuwest/modis-061-cogs'))['token']
    items=blob_inventory(year,token)
    days=sorted(set(i['properties']['start_datetime'][:10] for i in items))
    chosen={days[i] for i in np.linspace(0,len(days)-1,dates,dtype=int)}
    selected=[i for i in items if i['properties']['start_datetime'][:10] in chosen]
    count=0;ids=[]
    temp=output.with_suffix('.tmp')
    try:
        for item in selected:
            prop=item['properties'];mask=zones(prop['proj:wkt2'],tuple(prop['proj:transform']))
            arrays=[]
            for band in ['LST_Day_1km','QC_Day']:
                with MemoryFile(read(item['assets'][band]['href']+'?'+token)) as mem,mem.open() as raster:arrays.append(raster.read(1))
            raw,qc=arrays
            good=(mask>0)&qc_mask(raw,qc)
            r,c=np.where(good)
            frame=pd.DataFrame(dict(city=[FEATURES[i-1]['properties']['name'] for i in mask[good]],date=prop['start_datetime'][:10],tile=item['id'].split('.')[2],row=r,col=c,lst=raw[good]*.02-273.15,qc=qc[good]))
            frame.to_csv(temp,index=False,mode='a' if count else 'w',header=not bool(count),float_format='%.4f')
            count+=len(frame);ids.append(item['id']);print(len(ids),len(selected),count,flush=True)
        temp.replace(output)
    except Exception:
        temp.unlink(missing_ok=True);raise
    atomic_json(str(output)+'.source.json',dict(source='MOD11A2.061 Terra',scene_ids=ids,dates=sorted(chosen),rows=count,sha256=sha256(output),downloaded_at=now(),unit='real QC-filtered pixel; no duplication'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--year',type=int,default=2026);p.add_argument('--dates',type=int,default=3);a=p.parse_args();extract(a.output,a.year,a.dates)
