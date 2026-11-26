"""Validation before training, inference or replacing a verified data set."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
from registry import FEATURES, sha256

def validate(frame, mode='province'):
    required = {'city', 'date', *FEATURES[mode]}
    if not required.issubset(frame.columns):
        raise ValueError(f'Eksik veri sütunları: {sorted(required - set(frame.columns))}')
    df = frame.copy()
    df['date'] = pd.to_datetime(df.date, errors='raise')
    if df.empty or df.city.isna().any() or df.date.isna().any():
        raise ValueError('Boş veri veya eksik il/tarih')
    if df.duplicated(['city', 'date']).any():
        raise ValueError('Tekrarlanan il ve dönem')
    if not ((df.date.dt.dayofyear - 1) % 8 == 0).all() or (df.date.dt.dayofyear > 361).any():
        raise ValueError('MODIS kompozit başlangıç tarihi değil')
    for _, g in df.groupby('city', sort=False):
        if not g.date.is_monotonic_increasing:
            raise ValueError('İl dönemleri kronolojik sırada değil')
    if np.isinf(df[FEATURES[mode]].to_numpy(dtype=float)).any():
        raise ValueError('Sonsuz özellik değeri')
    if not df.lst.dropna().between(-90, 85).all():
        raise ValueError('LST fiziksel inceleme aralığı dışında (-90, 85 °C)')
    if mode == 'province':
        cols = {'scope', 'source', 'valid_fraction', 'valid_pixels', 'total_pixels', 'complete_tiles'}
        if not cols.issubset(df):
            raise ValueError('İl kalite/kaynak sütunları eksik')
        if set(df.scope) != {'province'} or not df.source.eq('MOD11A2.061 Terra').all():
            raise ValueError('İl ortalaması kaynağı veya kapsamı farklı')
        if df.complete_tiles.isna().any() or not pd.api.types.is_bool_dtype(df.complete_tiles):
            raise ValueError('complete_tiles boolean olmalı')
        counts = df[['valid_pixels', 'total_pixels']]
        if counts.isna().any().any() or (counts % 1 != 0).any().any():
            raise ValueError('Piksel sayıları tam sayı olmalı')
        if not (df.total_pixels > 0).all() or not df.valid_pixels.between(0, df.total_pixels).all():
            raise ValueError('Geçersiz piksel sayısı')
        if not df.valid_fraction.between(0, 1).all() or not np.allclose(df.valid_fraction, df.valid_pixels / df.total_pixels):
            raise ValueError('Geçerli piksel oranı tutarsız')
        bad = ~df.complete_tiles | (df.valid_fraction < .5) | (df.valid_pixels == 0)
        if df.loc[bad, 'lst'].notna().any():
            raise ValueError('Kalitesiz il gözlemi maskelenmemiş')
    return df

def report(path, mode='province'):
    df = validate(pd.read_csv(path), mode)
    return dict(source_file=str(path), sha256=sha256(path), rows=len(df), cities=df.city.nunique(),
                first_date=str(df.date.min().date()), last_date=str(df.date.max().date()),
                valid_lst=int(df.lst.count()), missing_lst=int(df.lst.isna().sum()))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('csv', type=Path)
    p.add_argument('--mode', choices=list(FEATURES), default='province')
    a = p.parse_args()
    print(json.dumps(report(a.csv, a.mode), ensure_ascii=False, indent=2))
