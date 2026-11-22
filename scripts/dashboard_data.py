"""Snapshot ve API için bölgesel gözlemler, uygun tahminler ve güncel deneyler."""
import json
from pathlib import Path
import pandas as pd
def rows(df):return json.loads(df.to_json(orient="records",double_precision=4,force_ascii=False))
def add(regions):
    for mode in ["uni","multi","common","province"]:
        path=Path(f"results/latest-{mode}.csv")
        if not path.exists():continue
        for city,g in pd.read_csv(path).groupby("city"):
            reg=regions.setdefault(city,{})
            reg.setdefault("runs",[]).extend(rows(g.assign(mode=mode)))
    path=Path("data/province-modis.csv")
    if path.exists():
        for city,g in pd.read_csv(path).sort_values("date").groupby("city"):
            reg=regions.setdefault(city,{})
            reg["provinceHistory"]=rows(g[["date","lst","valid_fraction","valid_pixels","total_pixels","complete_tiles"]])
    for path in [Path("results/summer-trial/scores.csv"),Path("results/gee-trial/scores.csv")]:
        if path.exists():
            for city,g in pd.read_csv(path).groupby("city"):
                regions.setdefault(city,{})["summerScores"]=rows(g)
