"""Evaluate frozen models on new observed targets, without retraining or publication."""
from pathlib import Path
import argparse
import json
import time
import os
os.environ.setdefault('KERAS_BACKEND','jax')
import joblib
import keras
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from data_quality import validate
from forecast import samples
from registry import verify,validate_preprocess,sha256
from spatial_train import metrics
from provenance import atomic_json,now

def evaluate(path,mode,out,start='2026-01-01'):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    df=validate(pd.read_csv(path),mode)
    frames=[];timings=[]
    for name in ['LSTM','XGBoost']:
        record=verify(mode,name);base=Path('models')/f'{mode}-{name}'
        meta=joblib.load(str(base)+'-preprocess.joblib');validate_preprocess(meta,record)
        X,y,keys=samples(df,meta['features'],record['training_end_year'],meta['window'])
        mask=(keys.date>=pd.Timestamp(start))&np.isfinite(y)&keys.baseline.notna()
        X=X[mask];y=y[mask];keys=keys.loc[mask].copy()
        width=X.shape[-1]
        X=np.nan_to_num(meta['scaler'].transform(X.reshape(-1,width)).reshape(X.shape)).astype('float32')
        started=time.perf_counter()
        if name=='LSTM':model=keras.models.load_model(str(base)+'.keras',compile=False)
        else:model=XGBRegressor();model.load_model(str(base)+'.json')
        load_seconds=time.perf_counter()-started
        values=X if name=='LSTM' else X.reshape(len(X),-1)
        started=time.perf_counter()
        pred=model.predict(values,verbose=0).ravel() if name=='LSTM' else model.predict(values)
        cold=time.perf_counter()-started
        started=time.perf_counter()
        again=model.predict(values,verbose=0).ravel() if name=='LSTM' else model.predict(values)
        warm=time.perf_counter()-started
        np.testing.assert_allclose(pred,again,rtol=1e-5,atol=1e-5)
        keys['actual']=y;keys['prediction']=pred*meta['scale']+meta['center'];keys['model']=name
        frames.append(keys);timings.append(dict(model=name,rows=len(keys),load_seconds=load_seconds,cold_prediction_seconds=cold,warm_prediction_seconds=warm,model_version=record['version']))
    baseline=frames[0].copy();baseline['model']='SeasonalNaive';baseline['prediction']=baseline.baseline
    frames.append(baseline);result=pd.concat(frames,ignore_index=True)
    result.to_csv(out/'backtest.csv',index=False)
    rows=[dict(city=city,h=int(h),model=model,**metrics(g.actual,g.prediction)) for (city,h,model),g in result.groupby(['city','h','model'])]
    pd.DataFrame(rows).to_csv(out/'scores.csv',index=False)
    pd.DataFrame(timings).to_csv(out/'timings.csv',index=False)
    previous=pd.read_json(f'results/temporal-{mode}.json')
    compared=pd.DataFrame(rows).merge(previous[['city','h','model','rmse']],on=['city','h','model'],suffixes=('_recent','_archive'),validate='one_to_one')
    compared['review']=compared.rmse_recent>compared.rmse_archive*1.25
    compared.to_csv(out/'performance-monitor.csv',index=False)
    atomic_json(out/'experiment.json',dict(created_at=now(),data_sha256=sha256(path),start=start,last_observed=str(df.date.max().date()),
        description='Frozen pre-2026 models; genuinely later observations, no retraining',models=timings,rows=len(result)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--mode',default='province');p.add_argument('--out',required=True);p.add_argument('--start',default='2026-01-01');a=p.parse_args()
    evaluate(a.data,a.mode,a.out,a.start)
