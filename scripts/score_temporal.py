"""Aynı il, başlangıç, hedef ve ufuktaki ölçümlerin eşleşmesini doğrula."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from spatial_train import metrics

KEY=["city","origin","date","h"]
def summarize(modes,out):
    frames=[]
    for mode in modes:
        df=pd.read_csv(f"results/backtest-{mode}.csv")
        pivot=df.pivot(index=KEY,columns="model",values="prediction")
        if set(pivot.columns)!={"SeasonalNaive","LSTM","XGBoost"} or pivot.isna().any().any():
            raise ValueError(f"{mode}: farklı test satırları")
        frames.append(df.assign(mode=mode))
    common=frames[0][KEY+["actual"]].drop_duplicates()
    for df in frames[1:]:
        both=common.merge(df[KEY+["actual"]].drop_duplicates(),on=KEY,validate="one_to_one")
        if len(both)!=len(common) or len(both)!=len(df[KEY].drop_duplicates()) or not np.allclose(both.actual_x,both.actual_y):
            raise ValueError("Girdi deneylerinin test anahtarları veya gerçek sıcaklıkları farklı")
    data=pd.concat(frames)
    data["season"]=pd.to_datetime(data.date).dt.month.map(lambda m:["Kış","İlkbahar","Yaz","Sonbahar"][(m%12)//3])
    rows=[]
    for by in [["city","h","model","mode"],["city","h","model","mode","season"]]:
        for key,g in data.groupby(by):
            stats=metrics(g.actual,g.prediction)
            ref=metrics(g.actual,g.baseline)["rmse"]
            rows.append(dict(zip(by,key),**stats,baseline_rmse=ref,improvement_pct=100*(1-stats["rmse"]/ref) if ref else None))
    pd.DataFrame(rows).to_csv(out,index=False)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--modes",nargs="+",default=["common","multi"])
    p.add_argument("--out",default="results/paired-seasons.csv")
    a=p.parse_args();summarize(a.modes,a.out)
