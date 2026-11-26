"""Kayıtlı modellerden son girişten sonraki dört MODIS kompozitine çıkarım."""
import os
os.environ.setdefault("KERAS_BACKEND","jax")
from check_environment import check
check()
import argparse
import joblib
import keras
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from forecast import calendar
from registry import verify, validate_preprocess
from data_quality import validate

def forecast(path,mode,models_dir="models",*,latest_valid=False):
    from pathlib import Path
    frame=validate(pd.read_csv(path),mode)
    output=[]
    for name in ["XGBoost","LSTM"]:
        record=verify(mode,name,Path(models_dir))
        base=f"{models_dir}/{mode}-{name}"
        meta=joblib.load(base+"-preprocess.joblib")
        validate_preprocess(meta,record)
        if name=="LSTM":
            model=keras.models.load_model(base+".keras",compile=False)
        else:
            model=XGBRegressor()
            model.load_model(base+".json")
        expected=(meta["window"],2*len(meta["features"])+1)
        if name=="LSTM" and tuple(model.input_shape[1:])!=expected:
            raise ValueError("LSTM giriş şekli manifest ile uyuşmuyor")
        if name=="XGBoost" and model.n_features_in_!=expected[0]*expected[1]:
            raise ValueError("XGBoost giriş genişliği manifest ile uyuşmuyor")
        inputs=[]
        records=[]
        for city,group in frame.groupby("city"):
            valid=group.loc[group.lst.notna(),"date"]
            if valid.empty: continue
            last=valid.max() if latest_valid else group.date.max()
            dates=calendar(last.year)
            index=dates.get_loc(last)
            features=meta["features"]
            window_size=meta["window"]
            if index+1<window_size: continue
            series=group.set_index("date").reindex(dates)[features]
            if not series.lst.iloc[max(0,index-3):index+1].notna().any():
                continue
            window=series.iloc[index-window_size+1:index+1]
            values=series.ffill(limit=3).iloc[index-window_size+1:index+1]
            for horizon in range(1,5):
                raw=np.c_[values,window.notna().astype(float),np.full(window_size,horizon/4)]
                normalized=meta["scaler"].transform(raw.astype("float32"))
                inputs.append(np.nan_to_num(normalized).astype("float32"))
                records.append(dict(city=city,origin=last.date(),date=dates[index+horizon].date(),
                                    h=horizon,model=name))
        if not inputs:
            continue
        batch=np.asarray(inputs)
        predictions=model.predict(batch,verbose=0).ravel() if name=="LSTM" else model.predict(batch.reshape(len(batch),-1))
        for record,prediction in zip(records,predictions):
            record["prediction"]=float(prediction)*meta["scale"]+meta["center"]
            output.append(record)
    return pd.DataFrame(output,columns=["city","origin","date","h","model","prediction"])

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("csv")
    parser.add_argument("--mode",default="uni",choices=["uni","multi","common","province"])
    parser.add_argument("--output",default="results/predictions.csv")
    args=parser.parse_args()
    forecast(args.csv,args.mode).to_csv(args.output,index=False)
