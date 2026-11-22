"""Gerçek veri üzerinde bağımsız süreçlerde süre ve tepe RSS ölçümü."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
import pandas as pd

def worker(path,engine,out):
    import resource
    import threading
    import psutil
    peak=[0]
    stop=threading.Event()
    process=psutil.Process()
    def sample():
        while not stop.wait(.1):
            total=0
            for proc in [process]+process.children(recursive=True):
                try:total+=proc.memory_info().rss
                except psutil.Error:pass
            peak[0]=max(peak[0],total)
    monitor=threading.Thread(target=sample,daemon=True)
    monitor.start()
    started=time.perf_counter()
    if engine=="pandas":
        df=pd.read_csv(path)
        df["year"]=pd.to_datetime(df.date).dt.year
        grouped=df.groupby(["city","year"]).lst.mean().reset_index()
    else:
        from pyspark.sql import SparkSession, functions as F
        spark=SparkSession.builder.master("local[2]").appName("LST Benchmark").getOrCreate()
        df=spark.read.option("header",True).csv(path)
        grouped=df.groupBy("city",F.year("date").alias("year")).agg(F.avg(F.col("lst").cast("double")).alias("lst")).toPandas()
        spark.stop()
    grouped.sort_values(["city","year"]).to_csv(out,index=False)
    stop.set(); monitor.join()
    stats=dict(seconds=time.perf_counter()-started,process_tree_peak_bytes=max(peak[0],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),python_peak_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               child_peak_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    Path(str(out)+".json").write_text(json.dumps(stats))

def main():
    p=argparse.ArgumentParser();p.add_argument("file");p.add_argument("--worker",choices=["pandas","spark"]);p.add_argument("--out");p.add_argument("--repeats",type=int,default=3)
    a=p.parse_args()
    if a.worker:worker(a.file,a.worker,a.out);return
    results=[]
    root=Path("results/benchmark");root.mkdir(exist_ok=True)
    for size in [.25,.5,1]:
        frame=pd.read_csv(a.file).sort_values(["date","city"]).iloc[:max(1,int(len(pd.read_csv(a.file))*size))]
        subset=root/f"subset-{size}.csv";frame.to_csv(subset,index=False)
        for repeat in range(a.repeats):
            for engine in ["pandas","spark"]:
                out=root/f"{size}-{repeat}-{engine}.csv"
                subprocess.run([sys.executable,__file__,str(subset),"--worker",engine,"--out",str(out)],check=True)
                results.append(dict(fraction=size,rows=len(frame),repeat=repeat,engine=engine,**json.loads(Path(str(out)+".json").read_text())))
            pd.testing.assert_frame_equal(pd.read_csv(root/f"{size}-{repeat}-pandas.csv"),
                                          pd.read_csv(root/f"{size}-{repeat}-spark.csv"),check_exact=False,rtol=1e-10,atol=1e-10)
        subset.unlink()
    pd.DataFrame(results).to_csv(root/"measurements.csv",index=False)
if __name__=="__main__":main()
