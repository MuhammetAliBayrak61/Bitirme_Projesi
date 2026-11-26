"""Export research figures and training-defined regional summaries."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from spatial_train import metrics

OUT=Path('results/revision/figures');OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})

def save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=180,bbox_inches='tight')
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight')
    plt.close(fig)

def main():
    fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
    for ax,(title,path) in zip(axes,[('2024–2025 archive','results/temporal-province.json'),('2026 new observations','results/revision/temporal-2026/scores.csv')]):
        df=pd.read_json(path) if path.endswith('.json') else pd.read_csv(path)
        for name,g in df.groupby('model'):
            mean=g.groupby('h').rmse.mean();ax.plot(mean.index*8,mean.values,marker='o',label=name)
        ax.set(title=title,xlabel='Nominal horizon (days)',ylabel='Mean of province RMSEs (°C)',xticks=[8,16,24,32]);ax.grid(alpha=.2);ax.legend()
    save(fig,'temporal-horizons')
    df=pd.read_csv('results/revision/diagnostics/spatial-error-slices.csv')
    df=df[(df.city=='Antalya')&(df.group=='B')&(df.model=='XGBoost')&(df.dimension=='heat_band')]
    fig,ax=plt.subplots(figsize=(6,4));ax.bar(df.category,df.bias,color=['#3b528b','#21918c']);ax.axhline(0,color='black',linewidth=.8);ax.set(ylabel='Mean prediction − observation (°C)',title='Antalya · retrospective error analysis');save(fig,'antalya-bias')
    frame=pd.read_csv('results/revision/benchmark-real/measurements.csv')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for name,g in frame.groupby('engine'):
        warm=g[g.phase=='warm_action'].groupby('rows').agg(seconds=('seconds','median'),rss=('peak_process_tree_bytes','max'))
        axes[0].plot(warm.index,warm.seconds,marker='o',label=name);axes[1].plot(warm.index,warm.rss/1024**2,marker='o',label=name)
    for ax,title,ylabel in zip(axes,['Warm repeated aggregation','Process tree memory'],['Seconds','Peak RSS (MiB)']):
        ax.set(xlabel='Distinct observed pixels',ylabel=ylabel,title=title);ax.legend();ax.grid(alpha=.2)
    save(fig,'benchmark-real-pixels')
    # Regions are learned from TRAINING observations only; no test labels and no claim of official climate classes.
    df=pd.read_csv('data/province-modis.csv');df['year']=pd.to_datetime(df.date).dt.year;df['month']=pd.to_datetime(df.date).dt.month
    train=df[df.year<=2022].groupby(['city','month']).lst.mean().unstack()
    summary=pd.DataFrame({'mean_lst':train.mean(axis=1),'annual_amplitude':train.max(axis=1)-train.min(axis=1)})
    summary['thermal_group']=KMeans(n_clusters=4,random_state=42,n_init=10).fit_predict(StandardScaler().fit_transform(summary)).astype(str)
    summary.to_csv(OUT/'training-thermal-groups.csv')
    test=pd.read_csv('results/backtest-province.csv').merge(summary[['thermal_group']],left_on='city',right_index=True,validate='many_to_one')
    scores=[dict(group=group,h=int(h),model=model,**metrics(g.actual,g.prediction)) for (group,h,model),g in test.groupby(['thermal_group','h','model'])]
    pd.DataFrame(scores).to_csv(OUT/'thermal-group-scores.csv',index=False)
    metadata={'thermal_groups':'Unsupervised grouping from 2018–2022 province mean LST and seasonal amplitude, not official climate zones.',
              'temporal_aggregation':'Unweighted mean of 81 city RMSE values for each horizon; not pooled RMSE.',
              'benchmark':'Same host, 2 local Spark threads, actual 2,666,362 pixels from 18 scenes; warm median from repeats 1 and 2.'}
    (OUT/'method.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
if __name__=='__main__':main()
