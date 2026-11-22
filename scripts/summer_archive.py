"""Yılda iki yaz tarihi ve dönüşümlü örnek alanlar; indirilen her sahne yeniden kullanılabilir."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import argparse
import time
import pandas as pd
from spatial_data import extract
from topography import sample

SITES={
    "Antalya":[("merkez",36.89,30.70),("saklikent",36.835,30.335),("elmali",36.735,29.92)],
    "Erzurum":[("merkez",39.90,41.27),("pasinler",39.98,41.67),("palandoken",39.83,41.28)],
    "İstanbul":[("esenler",41.05,28.86),("silivri",41.15,28.24),("beykoz",41.14,29.16)]}

def collect(task):
    city,site,year,month=task
    name,lat,lon=site
    dest=Path("cache/summer")/f"{city}-{name}-{year}-{month:02}.csv"
    if dest.exists(): return dest
    for attempt in range(2):
        try:
            extract(city,(lat,lon),year,month,dest)
            return dest
        except Exception:
            if attempt: raise
            time.sleep(2)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--workers",type=int,default=4)
    args=parser.parse_args()
    Path("cache/summer").mkdir(parents=True,exist_ok=True)
    tasks=[(city,sites[(year+i)%len(sites)],year,month) for year in range(2018,2026)
           for city,sites in SITES.items() for i,month in enumerate([6,8])]
    files=[]; failures=[]
    with ThreadPoolExecutor(args.workers) as pool:
        pending={pool.submit(collect,t):t for t in tasks}
        for job in as_completed(pending):
            try: files.append(job.result())
            except Exception as e:
                city,site,year,month=pending[job]
                failures.append(dict(city=city,site=site[0],year=year,month=month,error=type(e).__name__))
    # Bir yılda iki geçerli tarih oluşmadıysa Temmuz sahnesiyle kapsama ekle.
    preliminary=pd.concat([pd.read_csv(f) for f in files],ignore_index=True) if files else pd.DataFrame()
    if not preliminary.empty:
        valid=preliminary.dropna(subset=["lst","ndvi","ndbi"])
        for city,sites in SITES.items():
            for year in range(2018,2026):
                group=valid[(valid.city==city)&valid.date.str.startswith(str(year))]
                if group.date.nunique()<2:
                    try:files.append(collect((city,sites[0],year,7)))
                    except Exception as e:
                        failures.append(dict(city=city,site=sites[0][0],year=year,month=7,error=type(e).__name__))
    pd.DataFrame(failures,columns=["city","site","year","month","error"]).to_csv("results/summer-failures.csv",index=False)
    frames=[]
    for file in sorted(files):
        df=pd.read_csv(file);df["site"]=file.stem.split("-")[1]
        frames.append(df)
    if not frames: raise RuntimeError("Geçerli sahne indirilemedi.")
    df=pd.concat(frames,ignore_index=True)
    coords=df[["lat","lon"]].drop_duplicates().copy()
    coords[["height","slope"]]=[sample(r.lat,r.lon) for r in coords.itertuples()]
    df=df.merge(coords,on=["lat","lon"],validate="many_to_one")
    df.to_csv("data/summer.csv",index=False)
    print(len(files),"sahne",len(failures),"eksik",flush=True)
if __name__=="__main__": main()
