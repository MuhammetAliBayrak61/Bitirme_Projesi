"""Kayıtlı model için test edilmiş Python ve paket sürümlerini doğrular."""
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import sys

def check():
    problems=[]
    if sys.version_info[:2] != (3,12):
        problems.append("Python 3.12 gerekli. py -3.12 -m venv .venv")
    for line in (Path(__file__).resolve().parents[1]/"requirements.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):continue
        name,wanted=line.split("==")
        name=name.split("[")[0]
        try: installed=version(name)
        except PackageNotFoundError: installed="kurulu değil"
        if installed != wanted: problems.append(f"{name}: beklenen {wanted}, bulunan {installed}")
    if problems:
        raise RuntimeError("\n".join(problems)+"\n.venv Python ile pip install -r requirements.txt çalıştırın.")
if __name__=="__main__":
    import argparse,json,platform
    from datetime import datetime,timezone
    p=argparse.ArgumentParser();p.add_argument("--report",type=Path);a=p.parse_args()
    check()
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(dict(python=sys.version,platform=platform.platform(),
            time=datetime.now(timezone.utc).isoformat(),status="passed",
            packages={line.split("==")[0]:version(line.split("==")[0].split("[")[0]) for line in Path("requirements.txt").read_text().splitlines() if "==" in line}),indent=2),encoding="utf8")
    print("Python ve bağımlılık sürümleri uyumlu.")
