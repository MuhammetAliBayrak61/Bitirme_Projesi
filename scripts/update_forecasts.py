"""Güncel CSV verileriyle batch tahmin üret, kapsam/yeterlik kontrolü ve sürüm bilgisini yaz."""
from pathlib import Path
import argparse
import json
import os
import pandas as pd
from predict import forecast
from forecast import calendar

def run(mode,source):
    df=pd.read_csv(source,parse_dates=["date"])
    if df.duplicated(["city","date"]).any():raise ValueError("Tekrarlanan il ve dönem")
    if mode=="province":
        if "scope" not in df or set(df.scope)!={"province"}:raise ValueError("İl ortalaması gerekli")
        use=df.complete_tiles & (df.valid_fraction>=.5)
        df.loc[~use,"lst"]=float("nan")
        if not df.lst.equals(pd.read_csv(source).lst):raise ValueError("Kalite kontrolünden geçmeyen hedefleri önce maskeleyin")
    scores=pd.read_json(f"results/temporal-{mode}.json")
    output=forecast(source,mode)
    if output.empty:output=pd.DataFrame(columns=["city","h","model","date","origin","prediction"])
    output=output.merge(scores[["city","h","model","n","rmse"]],on=["city","h","model"],how="left",validate="many_to_one")
    info={}
    for m in ["XGBoost","LSTM"]:
        info[m]=json.loads(Path(f"models/{mode}-{m}-version.json").read_text(encoding="utf8"))
    for model,group in output.groupby("model"):
        output.loc[group.index,"version"]=info[model]["version"]
        output.loc[group.index,"trained_at"]=info[model]["trained_at"]
    # Son sekiz takvim döneminde en az dört gözlem ve eşleşmiş testte en az 12 örnek.
    coverage={}
    for city,g in df.groupby("city"):
        grid=calendar(g.date.max().year)
        end=grid.get_loc(g.date.max())
        coverage[city]=int(g.set_index("date").lst.reindex(grid[max(0,end-7):end+1]).count())
    output["recent_n"]=output.city.map(coverage)
    output["publishable"]=(output.recent_n>=4)&(output.n.fillna(0)>=12)&output.prediction.between(-50,85)
    output["scope"]="province" if mode=="province" else "point"
    path=Path(f"results/latest-{mode}.csv")
    tmp=path.with_suffix(".tmp");output.to_csv(tmp,index=False);os.replace(tmp,path)
    print(mode,len(output),int(output.publishable.sum()),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--mode",required=True,choices=["uni","multi","common","province"]);p.add_argument("--data",type=Path,required=True)
    a=p.parse_args();run(a.mode,a.data)
