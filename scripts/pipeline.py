"""Read-only change detection for the manual Airflow pipeline."""
import argparse
import json
from pathlib import Path
import pandas as pd
from province_archive import blob_inventory,read,PC,CACHE
from data_quality import report

def source_inventory(year):
    # Use the same public product inventory as the downloader, including late STAC indexing.
    token=json.loads(read(PC+'/sas/v1/token/modiseuwest/modis-061-cogs'))['token']
    return blob_inventory(year,token,refresh=True)

def plan(source):
    validated=report(source)
    CACHE.mkdir(parents=True,exist_ok=True)
    year=pd.Timestamp.now(tz='UTC').year
    items=source_inventory(year)
    last=max(i['properties']['start_datetime'][:10] for i in items)
    return dict(new_data=last>validated['last_date'],last_source=last,last_local=validated['last_date'],year=year,source_sha256=validated['sha256'])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='data/province-modis.csv');a=p.parse_args();print(json.dumps(plan(a.data)))
