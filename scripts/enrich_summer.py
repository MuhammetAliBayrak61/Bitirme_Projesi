"""Ölçülmüş hücre ve tarihlerde GEE Dynamic World ve ERA5-Land değerlerini çek."""
from pathlib import Path
import argparse
import ee
import pandas as pd
from rasterio.warp import transform
from earthengine_export import DW

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
    era=ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR").filterDate(date,date.advance(1,"day")).first()
    weather=ee.Image(era).select(["temperature_2m","dewpoint_temperature_2m"],["air","dew"]).subtract(273.15)
    stats=cover.addBands(weather).reduceRegions(collection=fc,reducer=ee.Reducer.mean(),scale=10,crs="EPSG:6933",tileScale=4)
    result=stats.map(lambda f:ee.Feature(None,f.toDictionary()))
    return pd.DataFrame([r["properties"] for r in result.getInfo()["features"]])
def main():
    p=argparse.ArgumentParser();p.add_argument("--project",required=True);a=p.parse_args()
    ee.Initialize(project=a.project)
    df=pd.read_csv("data/summer.csv")
    df["id"]=df.city+"|"+df.site+"|"+df.date+"|"+df.row.astype(str)+"|"+df.col.astype(str)
    parts=[]
    for key,g in df.groupby(["city","site","date","sentinel_date"]):
        path=Path("cache/gee-summer")/("-".join(key)+".csv");path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():
            values=fetch_scene(g)
            if set(values.id)!=set(g.id):raise ValueError("Hücre kimlikleri uyuşmuyor")
            tmp=path.with_suffix(".tmp");values.to_csv(tmp,index=False);tmp.replace(path)
        parts.append(pd.read_csv(path))
    df.merge(pd.concat(parts),on="id",validate="one_to_one").to_csv("data/summer-gee.csv",index=False)
if __name__=="__main__":main()
