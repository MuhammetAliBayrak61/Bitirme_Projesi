"""HTTP contract integration checks against an isolated seeded service."""
import argparse
import json
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import quote

def call(base,path):
    try:
        with urlopen(base+path,timeout=15) as r:return r.status,r.headers,json.load(r)
    except HTTPError as e:
        return e.code,e.headers,json.load(e)

def check(base):
    status,_,live=call(base,'/health/live');assert status==200 and live['status']=='alive'
    status,_,health=call(base,'/health');assert status==200 and health['status']=='ready'
    status,_,atlas=call(base,'/api/atlas');assert status==200 and len(atlas['features'])==81
    release=atlas['release']['id'];query_release=quote(release,safe='')
    status,_,names=call(base,'/api/iller');assert status==200 and len(names)==len(set(names))==81
    status,headers,province=call(base,'/api/iller/Antalya?release='+query_release);assert status==200 and headers['X-LST-Release']==release
    assert province['provinceHistory'] and province['runs'] and province['provinceScores']
    status,headers,layer=call(base,'/api/tahmin-katmani?release='+query_release);assert status==200 and headers['X-LST-Release']==release and layer
    for r in layer:assert r['publishable'] and r['scope']=='province' and len(r['version'])==64
    status,_,problem=call(base,'/api/iller/MISSING');assert status==404 and problem['status']==404
    status,_,problem=call(base,'/api/konum?lat=200&lon=30');assert status==400 and problem['status']==400
    status,_,problem=call(base,'/api/iller/Antalya?release=OLD');assert status==409
    status,_,problem=call(base,'/api/tahmin-katmani?release=OLD');assert status==409
    report=dict(status='passed',checks=10,release_id=release,cities=len(names),forecasts=len(layer))
    print(json.dumps(report,ensure_ascii=False))
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',default='http://127.0.0.1:5274');a=p.parse_args();check(a.base)
