"""Paired diagnostics, descriptive error analysis and drift; no model selection on test."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
from spatial_train import metrics
from confidence import interval
from registry import sha256
from provenance import atomic_json, now

def spatial(data,test_file,out):
    source=pd.read_csv(data)
    pred=pd.read_csv(test_file)
    keys=['city','date','lat','lon']
    extras=[c for c in source if c not in pred and c not in keys]
    joined=pred.merge(source[keys+extras],on=keys,validate='many_to_one')
    joined['year']=pd.to_datetime(joined.date).dt.year
    joined['surface_proxy']=np.select([joined.ndvi>=.5,joined.ndbi>0],['NDVI>=0.5','NDBI>0'],default='Diğer')
    joined['height_band']=pd.cut(joined.height,[-np.inf,500,1500,np.inf],labels=['<500m','500–1500m','>=1500m']).astype(str)
    joined['heat_band']=np.where(joined.lst>=45,'>=45C','<45C')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for field in ['year','site','surface_proxy','height_band','heat_band']:
        if field not in joined:continue
        for key,g in joined.groupby(['city','group','model',field],observed=True):
            rows.append(dict(city=key[0],group=key[1],model=key[2],dimension=field,category=str(key[3]),
                             bias=float((g.pred-g.lst).mean()),**metrics(g.lst,g.pred)))
    pd.DataFrame(rows).to_csv(out/'spatial-error-slices.csv',index=False)
    ci=[]
    for (city,group),part in joined.groupby(['city','group']):
        base=part[part.model=='Mean'][keys+['pred']].rename(columns={'pred':'baseline'})
        for model,g in part[part.model!='Mean'].groupby('model'):
            paired=g.merge(base,on=keys,validate='one_to_one').rename(columns={'pred':'prediction','lst':'actual'})
            # One whole acquisition date per cluster; keep correlated cells/sites together.
            blocks,lo,hi=interval(paired,'date')
            ci.append(dict(city=city,group=group,model=model,reference='training_mean',blocks=blocks,
                           low=lo,high=hi,block_definition='whole_scene_date',limited_clusters=blocks<10))
    pd.DataFrame(ci).to_csv(out/'spatial-confidence.csv',index=False)

def temporal(mode,out):
    df=pd.read_csv(f'results/backtest-{mode}.csv',parse_dates=['date'])
    keys=['city','origin','date','h']
    if df.duplicated(keys+['model']).any():raise ValueError('Tekrarlanan test anahtarı')
    pivot=df.pivot(index=keys,columns='model',values='prediction')
    if pivot.isna().any().any():raise ValueError('Eşleşmeyen test gözlemleri')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    df['season']=df.date.dt.month.map(lambda m:['Kış','İlkbahar','Yaz','Sonbahar'][(m%12)//3])
    df['heat_band']=np.where(df.actual>=35,'>=35C','<35C')
    scores=[];ci=[]
    for dimensions in [['city','h','model'],['city','h','model','season'],['city','h','model','heat_band']]:
        for key,g in df.groupby(dimensions):
            scores.append(dict(zip(dimensions,key),**metrics(g.actual,g.prediction)))
    pd.DataFrame(scores).to_csv(out/f'{mode}-scores.csv',index=False)
    for (city,h),part in df.groupby(['city','h']):
        for reference in ['SeasonalNaive','XGBoost']:
            baseline=part[part.model==reference][keys+['prediction']].rename(columns={'prediction':'reference'})
            for name,g in part[part.model!=reference].groupby('model'):
                paired=g.merge(baseline,on=keys,validate='one_to_one')
                paired['baseline']=paired.reference
                for days in [32,96,192]:
                    paired['block']=(paired.date-pd.Timestamp('2003-01-01')).dt.days//days
                    n,lo,hi=interval(paired,'block')
                    ci.append(dict(city=city,h=h,model=name,reference=reference,blocks=n,low=lo,high=hi,block_days=days,
                                   block_definition=f'{days}_day_nonoverlapping_target_blocks',limited_clusters=n<10,
                                   interpretation='exploratory_unadjusted_multiple_comparisons'))
    pd.DataFrame(ci).to_csv(out/f'{mode}-confidence.csv',index=False)
    if mode=='province':
        source=pd.read_csv('data/province-modis.csv')
        coverage=[]
        for city,g in source.groupby('city'):
            first=int(g.date.min()[:4]);last=int(g.date.max()[:4]);expected=(last-first+1)*46
            coverage.append(dict(city=city,rows=len(g),valid=int(g.lst.count()),expected_periods=expected,coverage=g.lst.count()/expected))
        pd.DataFrame(coverage).merge(pd.DataFrame(scores).query('season != season and heat_band != heat_band'),on='city').to_csv(out/'province-coverage-performance.csv',index=False)
    return df

def drift(reference,candidate,out):
    old=pd.read_csv(reference);new=pd.read_csv(candidate)
    boundary=old.date.max();new=new[new.date>boundary]
    rows=[]
    # Match calendar season so a winter-to-summer shift is not called climate drift.
    old['month']=pd.to_datetime(old.date).dt.month;new['month']=pd.to_datetime(new.date).dt.month
    for city,g in new.groupby('city'):
        train=old[(old.city==city)&old.date.str[:4].astype(int).le(2022)]
        for month,part in g.groupby('month'):
            ref=train[train.month==month]
            for feature in ['lst','ndvi','ndbi','valid_fraction']:
                if feature not in ref or feature not in part:continue
                a=ref[feature].dropna();b=part[feature].dropna()
                if len(a)<5 or len(b)<2:continue
                edges=np.unique(np.quantile(a,np.linspace(0,1,6)))
                if len(edges)<3:continue
                edges[0]=-np.inf;edges[-1]=np.inf
                p=np.histogram(a,edges)[0]+.5;q=np.histogram(b,edges)[0]+.5
                p=p/p.sum();q=q/q.sum();psi=float(((q-p)*np.log(q/p)).sum())
                fraction=float((~b.between(a.min(),a.max())).mean())
                rows.append(dict(city=city,month=int(month),feature=feature,reference_n=len(a),recent_n=len(b),
                    psi=psi,outside_train_range=fraction,review=bool(psi>.25 or fraction>.2),
                    note='heuristic_review_not_automatic_retraining'))
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(out,index=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('results/revision/diagnostics'))
    p.add_argument('--candidate',type=Path);a=p.parse_args()
    spatial('data/summer.csv','results/summer-trial/test.csv.gz',a.out)
    for mode in ['common','multi','province']:temporal(mode,a.out)
    if a.candidate:drift('data/province-modis.csv',a.candidate,a.out/'drift.csv')
    atomic_json(a.out/'method.json',dict(created_at=now(),seed=42,bootstrap_repeats=1000,
        intervals='paired RMSE differences; 95% percentile; no multiple-testing correction',
        surface_proxy='NDVI/NDBI thresholds are not Dynamic World labels',
        spatial_interpretation='Retrospective diagnostic; test data never used for hyperparameter selection'))
