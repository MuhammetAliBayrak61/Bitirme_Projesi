"""Generate a candidate forecast file; activation is a separate explicit action."""
from pathlib import Path
import argparse
import pandas as pd
from predict import forecast
from forecast import calendar
from registry import verify, sha256
from data_quality import validate

def run(mode, source, output, *, models_dir='models', scores_dir='results', as_of=None):
    df = validate(pd.read_csv(source), mode)
    scores = pd.read_json(Path(scores_dir) / f'temporal-{mode}.json')
    result = forecast(source, mode, models_dir, latest_valid=True)
    result = result.merge(scores[['city','h','model','n','rmse']], on=['city','h','model'], how='left', validate='many_to_one')
    for model, group in result.groupby('model'):
        info = verify(mode, model, Path(models_dir))
        result.loc[group.index, 'version'] = info['version']
        result.loc[group.index, 'trained_at'] = info['trained_at']
    coverage = {}
    for city, g in df.groupby('city'):
        valid = g.loc[g.lst.notna(), 'date']
        if valid.empty:
            coverage[city] = 0
            continue
        grid = calendar(valid.max().year)
        end = grid.get_loc(valid.max())
        coverage[city] = int(g.set_index('date').lst.reindex(grid[max(0,end-7):end+1]).count())
    result['recent_n'] = result.city.map(coverage)
    result['publishable'] = (result.recent_n >= 4) & (result.n.fillna(0) >= 12) & result.prediction.between(-50,85)
    today = pd.Timestamp(as_of or pd.Timestamp.now(tz='UTC').date())
    result['is_archived'] = pd.to_datetime(result.date) < today
    result['data_age_days'] = (today - pd.to_datetime(result.origin)).dt.days
    result['scope'] = 'province' if mode == 'province' else 'point'
    result['data_version'] = sha256(source)
    result['source_file'] = str(source)
    output = Path(output)
    if output.exists():
        raise FileExistsError(f'Aday çıktı zaten var: {output}')
    output.parent.mkdir(parents=True,exist_ok=True)
    result.to_csv(output,index=False)
    return result

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--mode', required=True, choices=['uni','multi','common','province'])
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--models-dir', default='models')
    a=p.parse_args()
    print(run(a.mode,a.data,a.output,models_dir=a.models_dir).shape)
