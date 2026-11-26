"""MOD11A2.061 Terra: yerel sinüzoidal piksel ızgarasında il alan ortalamaları."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import json
from pathlib import Path
from uuid import uuid4
import time
from urllib.parse import urlencode
from urllib.request import urlopen
import numpy as np
import pandas as pd
from affine import Affine
from rasterio.features import rasterize
from rasterio.io import MemoryFile
from rasterio.warp import transform_geom

PC="https://planetarycomputer.microsoft.com/api"
CACHE=Path("cache/province")
FEATURES=json.loads(Path("data/provinces.geojson").read_text(encoding="utf8"))["features"]
def read(url):
    for attempt in range(3):
        try:
            with urlopen(url,timeout=45) as r:return r.read()
        except Exception:
            if attempt==2:raise
            time.sleep(attempt+1)

def inventory(year,refresh=False):
    path=CACHE/f"items-{year}.json"
    if refresh or not path.exists():
        fields="id,properties.proj:transform,properties.proj:wkt2,properties.start_datetime,assets.QC_Day.href,assets.LST_Day_1km.href"
        params=dict(collections="modis-11A2-061",bbox="25,35.5,45,42.5",datetime=f"{year}-01-01/{year}-12-31",
                    limit=600,query=json.dumps({"platform":{"eq":"terra"}}),fields=fields)
        url=PC+"/stac/v1/search?"+urlencode(params)
        items=[]
        while url:
            page=json.loads(read(url))
            items.extend(f for f in page["features"] if f["id"].startswith("MOD11A2."))
            url=next((l["href"] for l in page.get("links",[]) if l["rel"]=="next"),None)
        if not items: raise ValueError(f"{year}: katalog boş")
        from provenance import atomic_json
        atomic_json(path,items)
    # Yeniden işlenmiş ürünlerde aynı tarih/karo için en son işleme sürümünü seç.
    unique={}
    for item in sorted(json.loads(path.read_text()),key=lambda v:v["id"]):
        if item["properties"]["start_datetime"].startswith(str(year)):
            unique[tuple(item["id"].split(".")[1:3])]=item
    return list(unique.values())

def blob_inventory(year,token,refresh=False):
    from xml.etree import ElementTree
    path=CACHE/f"verified-{year}.json"
    if path.exists() and not refresh:return json.loads(path.read_text())
    templates={f["id"].split(".")[2]:f["properties"] for f in inventory(2018)}
    container="https://modiseuwest.blob.core.windows.net/modis-061-cogs"
    selected={}
    for tile,template in templates.items():
        prefix=f"MOD11A2/{tile[1:3]}/{tile[4:]}/{year}"
        marker=""
        while True:
            params={"restype":"container","comp":"list","prefix":prefix,"marker":marker}
            page=ElementTree.fromstring(read(container+"?"+urlencode(params)+"&"+token))
            for node in page.findall("./Blobs/Blob/Name"):
                key=node.text
                if not key.endswith("_LST_Day_1km.tif"):continue
                scene=key.split("/")[-1].removesuffix("_LST_Day_1km.tif")
                doy=int(scene.split(".")[1][-3:])
                date=pd.Timestamp(year,1,1)+pd.Timedelta(days=doy-1)
                url=container+"/"+key
                item=dict(id=scene,properties={**template,"start_datetime":str(date.date())},
                          assets={"LST_Day_1km":{"href":url},"QC_Day":{"href":url.replace("_LST_Day_1km.tif","_QC_Day.tif")}})
                row=(tile,doy)
                if row not in selected or selected[row]["id"]<scene:selected[row]=item
            marker=page.findtext("NextMarker")
            if not marker:break
    items=list(selected.values())
    if not items:raise RuntimeError(f"{year} karoları eksik: {len(items)}")
    from provenance import atomic_json
    atomic_json(path,items)
    return items

@lru_cache(maxsize=9)
def zones(crs,affine):
    geoms=[(transform_geom("EPSG:4326",crs,f["geometry"]),i) for i,f in enumerate(FEATURES,1)]
    return rasterize(geoms,out_shape=(1200,1200),transform=Affine(*affine[:6]),dtype="uint8")

def process(item,token):
    path=CACHE/(item["id"]+".csv")
    if path.exists():return path
    p=item["properties"]
    mask=zones(p["proj:wkt2"],tuple(p["proj:transform"]))
    ids,counts=np.unique(mask,return_counts=True)
    def raster(band):
        url=item["assets"][band]["href"]
        with MemoryFile(read(url+"?"+token)) as mem,mem.open() as src:return src.read(1)
    raw=raster("LST_Day_1km")
    qc=raster("QC_Day")
    good=qc_mask(raw,qc)
    n=np.bincount(mask[good],minlength=82)
    total=np.bincount(mask[good],weights=raw[good]*.02-273.15,minlength=82)
    rows=[(FEATURES[i-1]["properties"]["name"],p["start_datetime"][:10],int(count),int(n[i]),total[i],item["id"].split(".")[2]) for i,count in zip(ids,counts) if i]
    df=pd.DataFrame(rows,columns=["city","date","pixels","valid_pixels","total_c","tile"])
    tmp=path.with_suffix("."+uuid4().hex+".tmp");df.to_csv(tmp,index=False);tmp.replace(path)
    return path
def qc_mask(raw,qc):
    return (raw>=9158)&(raw<=17907)&((qc&3)<=1)&(((qc>>2)&3)==0)&((qc>>6)<=1)
def combine(destination,baseline=None):
    latest={}
    for f in sorted(CACHE.glob("MOD11A2*.csv")):
        latest[tuple(f.name.split(".")[1:3])]=f
    paths=list(latest.values())
    if not paths: raise ValueError("İşlenmiş uydu karosu bulunamadı")
    df=pd.concat([pd.read_csv(p) for p in paths],ignore_index=True)
    if df.duplicated(["city","date","tile"]).any():raise ValueError("Yinelenen karo")
    # Bu coğrafi kapsam için her ilin tam piksel sayısını altı sabit karonun geometrisinden hesapla.
    items=json.loads(next(CACHE.glob("items-*.json")).read_text())
    grids={f["id"].split(".")[2]:f["properties"] for f in items}
    expected_tiles={f"h{h:02}v{v:02}" for h in [19,20,21] for v in [4,5]}
    if not expected_tiles.issubset(grids): raise ValueError("Referans ızgaraları eksik")
    counts=np.zeros(82,dtype=int)
    for key in expected_tiles:
        g=grids[key];counts+=np.bincount(zones(g["proj:wkt2"],tuple(g["proj:transform"])).ravel(),minlength=82)
    expected={f["properties"]["name"]:counts[i] for i,f in enumerate(FEATURES,1)}
    df=df.groupby(["city","date"],as_index=False)[["pixels","valid_pixels","total_c"]].sum()
    df["total_pixels"]=df.city.map(expected)
    df["valid_fraction"]=df.valid_pixels/df.total_pixels
    df["complete_tiles"]=df.pixels.eq(df.total_pixels)
    df["lst"]=(df.total_c/df.valid_pixels).where(df.complete_tiles & (df.valid_fraction>=.5))
    df["scope"]="province";df["source"]="MOD11A2.061 Terra"
    destination=Path(destination)
    if destination.exists():raise FileExistsError("Mevcut veri korunur; yeni --output yolu seçin")
    destination.parent.mkdir(parents=True,exist_ok=True)
    df=df.drop(columns=["total_c"]).sort_values(["city","date"])
    if baseline is not None:
        old=pd.read_csv(baseline)
        new_keys=set(zip(df.city,df.date))
        keep=[(c,d) not in new_keys for c,d in zip(old.city,old.date)]
        df=pd.concat([old.loc[keep],df],ignore_index=True).sort_values(["city","date"])
    from data_quality import validate
    validate(df,"province")
    temporary=destination.with_suffix("."+uuid4().hex+".tmp")
    df.to_csv(temporary,index=False)
    temporary.replace(destination)
    print("İl-dönem",len(df),"geçerli",df.lst.count(),flush=True)
def main():
    p=argparse.ArgumentParser();p.add_argument("--years",type=int,nargs="+",default=[pd.Timestamp.now().year]);p.add_argument("--workers",type=int,default=6);p.add_argument("--combine",action="store_true");p.add_argument("--reverse",action="store_true")
    p.add_argument("--output",type=Path,required=True);p.add_argument("--baseline",type=Path)
    a=p.parse_args();CACHE.mkdir(parents=True,exist_ok=True)
    if a.output.exists():raise FileExistsError("Aday çıktı zaten var")
    if a.combine:combine(a.output,a.baseline);return
    started=time.perf_counter()
    token=json.loads(read(PC+"/sas/v1/token/modiseuwest/modis-061-cogs"))["token"]
    with ThreadPoolExecutor(4) as ex:items=[v for batch in ex.map(lambda y:blob_inventory(y,token,refresh=True),a.years) for v in batch]
    # Her yılda farklı mevsimlere ait gözlemler baştan itibaren önbelleğe girer.
    items.sort(key=lambda v:(int(v["id"].split(".")[1][-3:])%32,v["id"].split(".")[1],v["id"]))
    if a.reverse: items.reverse()
    errors=[]
    with ThreadPoolExecutor(a.workers) as ex:
        jobs={ex.submit(process,i,token):i["id"] for i in items}
        for n,job in enumerate(as_completed(jobs),1):
            try:job.result()
            except Exception as e:
                reason=type(e).__name__+str(getattr(e,"code",""))
                errors.append((jobs[job],reason))
                if len(errors)<4: print(jobs[job],reason,str(e).split("?")[0][:90],flush=True)
            if n%100==0:print(n,len(items),"hata",len(errors),flush=True)
    from provenance import atomic_json, now
    audit=dict(source="Planetary Computer",product="MOD11A2.061 Terra",years=a.years,downloaded_at=now(),
        items=len(items),failures=errors,seconds=time.perf_counter()-started,
        qc="mandatory<=1,data_quality=0,LST_error<=2K; -90..85C; province_valid_fraction>=0.5")
    if errors:
        atomic_json(str(a.output)+".audit.json",dict(**audit,status="failed"))
        raise RuntimeError("İndirme hatası: mevcut veri korunuyor; önbellekten yeniden deneyin")
    combine(a.output,a.baseline)
    from data_quality import report
    atomic_json(str(a.output)+".audit.json",dict(**audit,status="validated_candidate",**report(a.output)))
if __name__=="__main__":main()
