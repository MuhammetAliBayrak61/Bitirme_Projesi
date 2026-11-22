"""Model ağırlıkları ve ölçekleyici aynı sürüm kimliğine dahildir."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json

def register(mode,name,scope,endtrain,last,features):
    base=Path("models")/f"{mode}-{name}"
    digest=hashlib.sha256()
    for file in [base.with_suffix(".keras" if name=="LSTM" else ".json"),Path(str(base)+"-preprocess.joblib")]:
        digest.update(file.read_bytes())
    record=dict(version=digest.hexdigest(),trained_at=datetime.now(timezone.utc).isoformat(),training_end_year=endtrain,
                archive_end=str(last.date()),model=name,mode=mode,scope=scope,features=features)
    Path(str(base)+"-version.json").write_text(json.dumps(record,indent=2),encoding="utf8")

def verify(mode,name):
    base=Path("models")/f"{mode}-{name}"
    version_file=Path(str(base)+"-version.json")
    if not version_file.exists():
        return None
    record=json.loads(version_file.read_text(encoding="utf8"))
    digest=hashlib.sha256()
    for file in [base.with_suffix(".keras" if name=="LSTM" else ".json"),Path(str(base)+"-preprocess.joblib")]:
        digest.update(file.read_bytes())
    if digest.hexdigest()!=record["version"]:
        raise ValueError(f"{base}: model ve ölçekleyici sürümü uyuşmuyor. Aynı eğitim koşusunun dosyalarını kullanın.")
    return record
