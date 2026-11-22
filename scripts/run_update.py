"""Eğitilmiş modellerden tahmin → snapshot → atomik veritabanı yayını."""
import argparse
from pathlib import Path
import subprocess
import sys
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--publish",action="store_true")
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    for mode,data in [("uni","modis.csv"),("multi","modis-multi.csv"),("common","modis-multi.csv"),("province","province-modis.csv")]:
        if (root/f"models/{mode}-LSTM-version.json").exists():
            subprocess.run([sys.executable,"scripts/update_forecasts.py","--mode",mode,"--data","data/"+data],cwd=root,check=True)
    subprocess.run([sys.executable,"scripts/snapshot.py"],cwd=root,check=True)
    if args.publish:subprocess.run([sys.executable,"scripts/publish.py"],cwd=root,check=True)
if __name__=="__main__": main()
