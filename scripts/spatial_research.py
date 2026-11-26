"""Aynı gözlemlerde il ve yıl dışarıda testi, referans ve dışdeğer tanısı."""
from pathlib import Path
import argparse
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression,Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from spatial_train import metrics

DW=["water","trees","grass","flooded_vegetation","crops","shrub_and_scrub","built","bare","snow_and_ice"]
GROUPS={"A":["ndvi","ndbi"],"B":["height","slope"],"C":DW,"D":["air","dew"]}
def fit(data,out,original=False,require_all=False):
    df=data.copy()
    df["year"]=pd.to_datetime(df.date).dt.year
    fields=[];groups={}
    for name,columns in GROUPS.items():
        if not set(columns)<=set(df.columns):break
        fields+=columns;groups[name]=fields.copy()
    if require_all and set(groups)!={"A","B","C","D"}:
        raise ValueError("A/B/C/D karşılaştırması için tüm Dynamic World ve ERA5 sütunları gerekli.")
    required=["lst","date","lat","lon","city"]+fields
    df=df.replace([np.inf,-np.inf],np.nan).dropna(subset=required)
    if df.duplicated(["city","date","lat","lon"]).any():raise ValueError("Yinelenen hücre/tarih")
    if set(df.city)!={"Antalya","Erzurum","İstanbul"}:raise ValueError("Üç pilot için geçerli veri gerekli")
    if out.exists():raise FileExistsError("Deney arşivi korunur; yeni bir çıktı klasörü seçin")
    out.mkdir(parents=True,exist_ok=False)
    from spatial_validation import blocks,splits,select
    from provenance import atomic_json,now
    scores=[];ranges=[];tests=[];validation=[];partition=[]
    df.groupby(["city","date"],as_index=False).size().to_csv(out/"coverage.csv",index=False)
    for city in sorted(df.city.unique()):
        train=df[df.city!=city];test=df[df.city==city]
        if not original:
            train=train[train.year<=2023];test=test[test.year.between(2024,2025)]
        if train.empty or test.empty:raise ValueError(f"{city}: eğitime veya bağımsız teste veri yok.")
        for split,frame in [("train",train),("test",test)]:
            partition.append(frame[["city","date","lat","lon"]].assign(held_out_city=city,split=split,block=blocks(frame)))
        if not original:
            for fold,(a,b) in enumerate(splits(train)):
                for split,idx in [("inner_train",a),("validation",b)]:
                    frame=train.iloc[idx]
                    partition.append(frame[["city","date","lat","lon"]].assign(held_out_city=city,split=split,fold=fold,block=blocks(frame)))
        for col in fields+["lst"]:
            lo,hi=train[col].min(),train[col].max()
            ranges.append(dict(city=city,feature=col,train_min=lo,train_max=hi,test_min=test[col].min(),
                               test_max=test[col].max(),outside_fraction=(~test[col].between(lo,hi)).mean()))
        for group,features in groups.items():
            models={"Mean":DummyRegressor(),"LinearRegression":LinearRegression(),
                    "Ridge":make_pipeline(StandardScaler(),Ridge(alpha=10)),
                    "RandomForest":RandomForestRegressor(n_estimators=80,min_samples_leaf=5,n_jobs=2,random_state=42),
                    "XGBoost":XGBRegressor(n_estimators=120,max_depth=3,n_jobs=2,learning_rate=.07,random_state=42)}
            for name,model in models.items():
                if not original:
                    model,records=select(model,name,train,features,city,group);validation.extend(records)
                model.fit(train[features],train.lst)
                pred=model.predict(test[features])
                suspicious=(pred<-50)|(pred>85)
                scores.append(dict(city=city,group=group,model=name,train_n=len(train),train_high_1500=int((train.height>=1500).sum()),
                    test_years=",".join(map(str,sorted(test.year.unique()))),pred_min=pred.min(),pred_max=pred.max(),
                    outside_review_range=int(suspicious.sum()),**metrics(test.lst,pred)))
                tests.append(test[["city","date","lat","lon","lst"]].assign(group=group,model=name,pred=pred,review=suspicious))
                if not original and name!="Mean":
                    joblib.dump(model,out/f"{city}-{group}-{name}.joblib",compress=3)
    pd.DataFrame(scores).to_csv(out/"scores.csv",index=False)
    pd.DataFrame(ranges).to_csv(out/"ranges.csv",index=False)
    pd.concat(tests,ignore_index=True).to_csv(out/"test.csv.gz",index=False)
    pd.DataFrame(validation).to_csv(out/"validation.csv",index=False)
    pd.concat(partition,ignore_index=True).to_csv(out/"split-manifest.csv.gz",index=False)
    atomic_json(out/"experiment.json",dict(created_at=now(),seed=42,groups=groups,rows_before=len(data),rows_complete=len(df),
        split="held-out city AND held-out 2024-2025; inner validation groups all dates of site",selection="training_only",
        interpretation="Existing test period; exploratory reanalysis, not a new confirmation set"))
def main():
    p=argparse.ArgumentParser();p.add_argument("--data",type=Path);p.add_argument("--out",type=Path,required=True)
    p.add_argument("--original",action="store_true")
    p.add_argument("--require-all",action="store_true")
    args=p.parse_args()
    df=pd.read_csv(args.data) if args.data and args.data.is_file() else pd.concat([pd.read_csv(f) for f in (args.data or Path("data")).glob("spatial-*.csv")],ignore_index=True)
    fit(df,args.out,args.original,args.require_all)
if __name__=="__main__":main()
