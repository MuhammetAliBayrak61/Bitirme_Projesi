"""Distinct real rows; separate session startup, first action and warmed actions."""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

def worker(path,engine,out,repeats):
    import threading
    import psutil
    proc=psutil.Process();peak=[0];stop=threading.Event()
    def sample():
        while not stop.wait(.05):
            total=0
            for p in [proc]+proc.children(recursive=True):
                try:total+=p.memory_info().rss
                except psutil.Error:pass
            peak[0]=max(peak[0],total)
    def cpu():
        total=0
        for p in [proc]+proc.children(recursive=True):
            try:t=p.cpu_times();total+=t.user+t.system
            except psutil.Error:pass
        return total
    monitor=threading.Thread(target=sample,daemon=True);monitor.start()
    started=time.perf_counter()
    if engine=='spark':
        from pyspark.sql import SparkSession,functions as F
        spark=SparkSession.builder.master('local[2]').appName('LST-real-pixels').config('spark.driver.bindAddress','127.0.0.1').config('spark.driver.host','127.0.0.1').config('spark.ui.enabled','false').config('spark.sql.shuffle.partitions','4').getOrCreate()
    else:
        import pandas as pd
    startup=time.perf_counter()-started
    records=[]
    for repeat in range(repeats):
        beginning=time.perf_counter();cpu_start=cpu();peak[0]=0
        if engine=='pandas':
            frame=pd.read_csv(path,usecols=['city','date','lst'])
            grouped=frame.groupby(['city','date'],as_index=False).lst.mean()
        else:
            frame=spark.read.schema('city STRING,date STRING,tile STRING,row INT,col INT,lst DOUBLE,qc INT').option('header',True).csv(path)
            grouped=frame.groupBy('city','date').agg(F.avg('lst').alias('lst')).toPandas()
        grouped.sort_values(['city','date']).to_csv(str(out)+f'.{repeat}.csv',index=False)
        records.append(dict(repeat=repeat,phase='first_action' if repeat==0 else 'warm_action',seconds=time.perf_counter()-beginning,
            cpu_seconds=cpu()-cpu_start,peak_process_tree_bytes=peak[0],startup_seconds=startup))
    if engine=='spark':spark.stop()
    stop.set();monitor.join()
    Path(out).write_text(json.dumps(records,indent=2))

def main():
    p=argparse.ArgumentParser();p.add_argument('file');p.add_argument('--worker',choices=['pandas','spark']);p.add_argument('--out',required=True);p.add_argument('--repeats',type=int,default=3);a=p.parse_args()
    if a.repeats<3:p.error('En az 3 tekrar gerekli')
    if a.worker:worker(a.file,a.worker,a.out,a.repeats);return
    import pandas as pd
    from provenance import atomic_json,now
    from registry import sha256
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False)
    frame=pd.read_csv(a.file)
    if frame.duplicated(['tile','date','row','col']).any():raise ValueError('Benchmark gerçek ve benzersiz piksel kayıtları gerektirir')
    stats=[]
    for fraction in [.1,.5,1.]:
        subset=root/f'input-{fraction}.csv';frame.iloc[:max(1,int(len(frame)*fraction))].to_csv(subset,index=False)
        for engine in ['pandas','spark']:
            result=root/f'{fraction}-{engine}.json';start=time.perf_counter()
            subprocess.run([sys.executable,__file__,str(subset),'--worker',engine,'--out',str(result),'--repeats',str(a.repeats)],check=True)
            elapsed=time.perf_counter()-start
            stats.extend(dict(engine=engine,fraction=fraction,rows=int(len(frame)*fraction),process_wall_seconds=elapsed,**r) for r in json.loads(result.read_text()))
        for repeat in range(a.repeats):
            pd.testing.assert_frame_equal(pd.read_csv(str(root/f'{fraction}-pandas.json')+f'.{repeat}.csv'),pd.read_csv(str(root/f'{fraction}-spark.json')+f'.{repeat}.csv'),check_exact=False,atol=1e-9,rtol=1e-9)
        subset.unlink()
    pd.DataFrame(stats).to_csv(root/'measurements.csv',index=False)
    atomic_json(root/'environment.json',dict(time=now(),input_sha256=sha256(a.file),python=sys.version,platform=platform.platform(),logical_cpus=os.cpu_count(),spark_threads=2,
        source='distinct real MODIS pixels; never duplicated to inflate row count',method='read CSV + group city/date + mean LST + materialize output; no persisted Spark cache'))
if __name__=='__main__':main()
