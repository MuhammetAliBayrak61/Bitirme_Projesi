"""Atomic provenance records. No connection strings or signed URLs."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
from uuid import uuid4
from registry import sha256

def now():
    return datetime.now(timezone.utc).isoformat()

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
    try:
        temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)

def inputs(paths):
    return {str(p): sha256(p) for p in map(Path, paths) if p.is_file()}
