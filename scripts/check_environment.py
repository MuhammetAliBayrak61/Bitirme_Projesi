"""Kayıtlı model için test edilmiş Python ve paket sürümlerini doğrular."""
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import sys

def check():
    problems=[]
    if sys.version_info[:2] != (3,12):
        problems.append("Python 3.12 gerekli. py -3.12 -m venv .venv")
    for line in (Path(__file__).resolve().parents[1]/"requirements.txt").read_text().splitlines():
        name,wanted=line.split("==")
        name=name.split("[")[0]
        try: installed=version(name)
        except PackageNotFoundError: installed="kurulu değil"
        if installed != wanted: problems.append(f"{name}: beklenen {wanted}, bulunan {installed}")
    if problems:
        raise RuntimeError("\n".join(problems)+"\n.venv Python ile pip install -r requirements.txt çalıştırın.")
if __name__=="__main__":
    check()
    print("Python ve bağımlılık sürümleri uyumlu.")
