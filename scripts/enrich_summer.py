"""Ölçülmüş hücre ve tarihlerde GEE Dynamic World ve ERA5-Land değerlerini çek."""
from pathlib import Path
import argparse
import ee
import pandas as pd
import numpy as np
from rasterio.warp import transform
from earthengine_export import DW

def validate_features(frame):
    required={"id",*DW,"air","dew"}
    if not required.issubset(frame):raise ValueError("C/D özellik sütunları eksik")
    if frame.id.isna().any() or frame.id.duplicated().any():raise ValueError("Hücre kimliği eksik/yinelenmiş")
    values=frame[DW].dropna()
    if not values.empty and (not values.ge(0).all().all() or not values.le(1).all().all() or not np.allclose(values.sum(axis=1),1,atol=1e-3)):
        raise ValueError("Dynamic World olasılıkları 0..1 aralığında ve toplamı 1 olmalı")
    weather=frame[["air","dew"]].dropna()
    if not weather.empty and (not weather.air.between(-90,65).all() or not weather.dew.between(-110,65).all() or (weather.dew>weather.air+.5).any()):
        raise ValueError("ERA5 birimi veya sıcaklık/çiy noktası tutarsız")
    return dict(rows=len(frame),complete=int(frame[list(required)].notna().all(axis=1).sum()),
                missing_fraction=frame[[*DW,"air","dew"]].isna().mean().to_dict())

def fetch_scene(rows):
    rows=rows.copy()
    date=ee.Date(rows.date.iloc[0]);optic=ee.Date(rows.sentinel_date.iloc[0])
    points=[]
    for row in rows.itertuples():
        crs=f"EPSG:{32601+int((row.lon+180)//6)}"
        x,y=transform("EPSG:4326",crs,[row.lon],[row.lat])
        geom=ee.Geometry.Rectangle([x[0]-150,y[0]-150,x[0]+150,y[0]+150],proj=crs,geodesic=False)
        points.append(ee.Feature(geom,{"id":row.id}))
    fc=ee.FeatureCollection(points)
    imgs=ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(fc.geometry()).filterDate(optic,optic.advance(1,"day")).select(DW)
    blank=ee.Image.constant([0]*len(DW)).rename(DW).selfMask()
    cover=imgs.merge(ee.ImageCollection([blank])).mean()
    eras=ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR").filterDate(date,date.advance(1,"day"))
    if eras.size().getInfo()==0:raise ValueError("İstenen tarihte ERA5 gözlemi yok")
    era=eras.first()
    weather=ee.Image(era).select(["temperature_2m","dewpoint_temperature_2m"],["air","dew"]).subtract(273.15)
    stats=cover.addBands(weather).reduceRegions(collection=fc,reducer=ee.Reducer.mean(),scale=10,crs="EPSG:6933",tileScale=4)
    result=stats.map(lambda f:ee.Feature(None,f.toDictionary()))
    return pd.DataFrame([r["properties"] for r in result.getInfo()["features"]])
def main():
    p=argparse.ArgumentParser();p.add_argument("--project",required=True)
    p.add_argument("--city");p.add_argument("--date");p.add_argument("--limit-scenes",type=int)
    p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError("Mevcut veri korunur; yeni --output seçin")
    ee.Initialize(project=a.project)
    df=pd.read_csv("data/summer.csv")
    if a.city:df=df[df.city==a.city]
    if a.date:df=df[df.date==a.date]
    if df.empty:raise ValueError("Seçilen il/tarih için sahne yok")
    df["id"]=df.city+"|"+df.site+"|"+df.date+"|"+df.row.astype(str)+"|"+df.col.astype(str)
    parts=[];selected=[]
    import hashlib
    for i,(key,g) in enumerate(df.groupby(["city","site","date","sentinel_date"])):
        if a.limit_scenes is not None and i>=a.limit_scenes:break
        identity=hashlib.sha256(g.to_csv(index=False).encode()).hexdigest()[:16]
        path=Path("cache/gee-summer")/("-".join(key)+"-"+identity+".csv");path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():
            values=fetch_scene(g)
            if set(values.id)!=set(g.id):raise ValueError("Hücre kimlikleri uyuşmuyor")
            validate_features(values)
            tmp=path.with_suffix(".tmp");values.to_csv(tmp,index=False);tmp.replace(path)
        values=pd.read_csv(path)
        if set(values.id)!=set(g.id):raise ValueError("Önbellek hücreleri uyuşmuyor")
        validate_features(values);parts.append(values);selected.append(g)
    merged=pd.concat(selected).merge(pd.concat(parts),on="id",validate="one_to_one")
    report=validate_features(merged)
    if report["complete"]==0:raise ValueError("Tam C/D gözlemi bulunamadı")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    from provenance import atomic_json,now
    from registry import sha256
    tmp=a.output.with_suffix(".tmp");merged.to_csv(tmp,index=False);tmp.replace(a.output)
    atomic_json(str(a.output)+".audit.json",dict(**report,source_sha256=sha256("data/summer.csv"),
        output_sha256=sha256(a.output),downloaded_at=now(),dw_source="GOOGLE/DYNAMICWORLD/V1",era_source="ECMWF/ERA5_LAND/DAILY_AGGR",
        spatial_resolution="DW 10m averaged inside 300m cell; ERA5 native ~11km, not independent 300m weather",
        date_matching="DW Sentinel acquisition date; ERA5 Landsat acquisition date",temperature_unit="C"))
if __name__=="__main__":main()
