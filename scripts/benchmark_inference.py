"""Inference CPU/RSS including process children; frozen models, no artifact mutation."""
import argparse
from pathlib import Path
import subprocess
import sys
import time
import json
import psutil
from provenance import atomic_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--out',required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
    if a.worker:
        from predict import forecast
        start=time.perf_counter();result=forecast(a.data,'province',latest_valid=True)
        print(json.dumps(dict(rows=len(result),seconds=time.perf_counter()-start)));return
    command=[sys.executable,__file__,'--data',a.data,'--out',a.out,'--worker']
    start=time.perf_counter();child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    process=psutil.Process(child.pid);peak=0;cpu=0
    while child.poll() is None:
        memory=0;used=0
        for proc in [process]+process.children(recursive=True):
            try:
                memory+=proc.memory_info().rss;c=proc.cpu_times();used+=c.user+c.system
            except psutil.Error:pass
        peak=max(peak,memory);cpu=max(cpu,used);time.sleep(.05)
    stdout,stderr=child.communicate()
    if child.returncode:raise RuntimeError(stderr)
    atomic_json(a.out,dict(batched_two_model_inference=json.loads(stdout.strip().splitlines()[-1]),process_wall_seconds=time.perf_counter()-start,peak_process_tree_bytes=peak,cpu_seconds=cpu,
        per_model_timings='results/revision/temporal-2026/timings.csv',scope='Combined CLI process incl. Python/JAX/model load; RSS not GPU memory'))
if __name__=='__main__':main()
