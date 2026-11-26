"""External Köppen–Geiger grouping for evaluation; never a fitted model feature.

Input: Beck et al. (2018), present-day 1980–2016 GeoTIFF, CC BY 4.0.
Classification is not an official Turkish administrative climate assignment.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.windows import from_bounds
from provenance import atomic_json,now
from registry import sha256
from spatial_train import metrics

SYMBOLS='Af Am Aw BWh BWk BSh BSk Csa Csb Csc Cwa Cwb Cwc Cfa Cfb Cfc Dsa Dsb Dsc Dsd Dwa Dwb Dwc Dwd Dfa Dfb Dfc Dfd ET EF'.split()

def summarize(codes,zones,transform,names):
    if np.any((codes<0)|(codes>30)):
        raise ValueError('Beklenmeyen Köppen sınıf kodu')
    # Exact relative spherical area of each regular latitude row.
    edges=transform.f+np.arange(codes.shape[0]+1)*transform.e
    area=np.abs(np.sin(np.deg2rad(edges[:-1]))-np.sin(np.deg2rad(edges[1:])))
    weights=np.broadcast_to(area[:,None],codes.shape)
    rows=[];fractions=[]
    for i,city in enumerate(names,1):
        mask=zones==i;valid=mask&(codes>0)
        total=weights[mask].sum();observed=weights[valid].sum()
        if total<=0 or observed<=0:
            raise ValueError(f'{city}: iklim rasterı kapsamı yok')
        sizes=np.bincount(codes[valid],weights=weights[valid],minlength=31)
        dominant=int(sizes.argmax())
        rows.append(dict(city=city,climate=SYMBOLS[dominant-1],code=dominant,
            mixed_classes=bool(sizes[dominant]/observed<.5),
            dominant_fraction=float(sizes[dominant]/observed),mapped_fraction=float(observed/total)))
        for code in np.flatnonzero(sizes):
            fractions.append(dict(city=city,climate=SYMBOLS[code-1],fraction=float(sizes[code]/observed)))
    return pd.DataFrame(rows),pd.DataFrame(fractions)

def evaluate(raster,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    features=json.loads(Path('data/provinces.geojson').read_text(encoding='utf8'))['features']
    names=[f['properties']['name'] for f in features]
    with rasterio.open(raster) as src:
        if src.crs!=rasterio.crs.CRS.from_epsg(4326) or src.count!=1:
            raise ValueError('EPSG:4326 tek bant raster bekleniyor')
        window=from_bounds(25,35,45,43,src.transform).round_offsets().round_lengths()
        codes=src.read(1,window=window);transform=src.window_transform(window)
        profile={**src.profile,'height':codes.shape[0],'width':codes.shape[1],'transform':transform,'compress':'deflate'}
        with rasterio.open(out/'koppen-1980-2016-turkiye.tif','w',**profile) as dst:dst.write(codes,1)
    zones=rasterize([(f['geometry'],i) for i,f in enumerate(features,1)],out_shape=codes.shape,transform=transform,dtype='uint8')
    groups,fractions=summarize(codes,zones,transform,names)
    assert len(groups)==81 and groups.city.is_unique
    assert np.allclose(fractions.groupby('city').fraction.sum(),1)
    groups.to_csv(out/'province-climate.csv',index=False)
    fractions.to_csv(out/'province-climate-fractions.csv',index=False)
    outputs=[];matching=[]
    keys=['city','origin','date','h'];models=['LSTM','XGBoost','SeasonalNaive']
    for period,path in [('2024-2025','results/backtest-province.csv'),('2026','results/revision/temporal-2026/backtest.csv')]:
        df=pd.read_csv(path);common=None
        for model in models:
            subset=df[df.model==model]
            if subset.duplicated(keys).any():raise ValueError('Tekrarlanan test tahmini')
            index=pd.MultiIndex.from_frame(subset[keys])
            common=index if common is None else common.intersection(index)
        df=df[df.model.isin(models)&pd.MultiIndex.from_frame(df[keys]).isin(common)]
        matching.append(dict(period=period,matched_targets=len(common),models=models))
        df=df.merge(groups[['city','climate']],on='city',validate='many_to_one')
        for (climate,h,model),g in df.groupby(['climate','h','model']):
            outputs.append(dict(period=period,climate=climate,h=int(h),model=model,cities=g.city.nunique(),
                few_cities=bool(g.city.nunique()<5),**metrics(g.actual,g.prediction)))
    pd.DataFrame(outputs).to_csv(out/'climate-scores.csv',index=False)
    atomic_json(out/'method.json',dict(created_at=now(),source='Beck et al. 2018, Köppen–Geiger 1980–2016',
        doi='10.6084/m9.figshare.6396959.v2',paper='10.1038/sdata.2018.214',license='CC BY 4.0',
        raster_sha256=sha256(raster),crop_sha256=sha256(out/'koppen-1980-2016-turkiye.tif'),
        boundaries_sha256=sha256('data/provinces.geojson'),resolution_degrees=[transform.a,abs(transform.e)],
        method='Pixel-centre boundary assignment; spherical area-weighted majority class per province; pooled metrics on matched targets.',
        limitations=['Not an official MGM classification; Natural Earth simplified boundaries.',
            'A province may span multiple classes; fractions retained. Static 1980–2016 baseline.',
            'Stratified temporal test, not leave-climate-zone-out validation. Classes with <5 cities flagged.'],
        matching=matching))
    print(groups.groupby('climate').size().to_string())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raster',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    evaluate(a.raster,a.out)
