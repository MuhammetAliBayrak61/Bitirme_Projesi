"""Trusted project artifacts only. Checksums prove integrity, not publisher identity."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

FEATURES = {'uni': ['lst'], 'common': ['lst'], 'province': ['lst'],
            'multi': ['lst', 'ndvi', 'ndbi', 'height', 'slope', 'air', 'dew']}

def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def artifacts(mode, name, root=Path('models')):
    if mode not in FEATURES or name not in ('LSTM', 'XGBoost'):
        raise ValueError('Bilinmeyen model veya kapsam')
    base = root / f'{mode}-{name}'
    return [base.with_suffix('.keras' if name == 'LSTM' else '.json'),
            Path(str(base) + '-preprocess.joblib')], Path(str(base) + '-version.json')

def combined(files):
    digest = hashlib.sha256()
    for file in files:
        if not file.is_file():
            raise ValueError(f'Model dosyası eksik: {file}')
        digest.update(file.read_bytes())
    return digest.hexdigest()

def verify(mode, name, root=Path('models')):
    files, manifest = artifacts(mode, name, root)
    if not manifest.is_file():
        raise ValueError(f'Model sürüm dosyası eksik: {manifest}; çıkarım reddedildi.')
    try:
        record = json.loads(manifest.read_text(encoding='utf8'))
    except (ValueError, OSError) as exc:
        raise ValueError(f'Bozuk model sürüm dosyası: {manifest}') from exc
    if not isinstance(record, dict) or record.get('version') != combined(files):
        raise ValueError(f'{manifest}: model ve ölçekleyici sürümü uyuşmuyor.')
    scope = 'province' if mode == 'province' else 'point'
    for key, value in {'mode': mode, 'model': name, 'scope': scope, 'features': FEATURES[mode]}.items():
        if record.get(key) != value:
            raise ValueError(f'Model giriş şeması uyuşmuyor: {key}')
    if not record.get('trained_at') or not isinstance(record.get('training_end_year'), int):
        raise ValueError('Model eğitim bilgisi eksik')
    # Original v1 hashes include BOTH files. Do not rewrite archived models.
    schema = record.get('schema_version', 1)
    if schema not in (1, 2):
        raise ValueError('Desteklenmeyen model manifest şeması')
    if schema == 2:
        if record.get('files') != {p.name: sha256(p) for p in files}:
            raise ValueError('Model/ön işleme SHA-256 doğrulaması başarısız')
        if not isinstance(record.get('window'), int) or record['window'] < 1:
            raise ValueError('Geçersiz giriş pencere uzunluğu')
        if record.get('input_width') != 2 * len(FEATURES[mode]) + 1:
            raise ValueError('Geçersiz giriş genişliği')
    return record

def validate_preprocess(meta, record):
    import numpy as np
    width = 2 * len(record['features']) + 1
    if meta.get('features') != record['features']:
        raise ValueError('Ön işleme özellik şeması uyuşmuyor')
    if not isinstance(meta.get('window'), int) or meta['window'] < 1:
        raise ValueError('Geçersiz pencere uzunluğu')
    if record.get('window', meta['window']) != meta['window']:
        raise ValueError('Ön işleme pencere şeması uyuşmuyor')
    if getattr(meta.get('scaler'), 'n_features_in_', None) != width:
        raise ValueError('Ölçekleyici giriş genişliği uyuşmuyor')
    if not np.isfinite(meta.get('scale', np.nan)) or meta['scale'] <= 0 or not np.isfinite(meta.get('center', np.nan)):
        raise ValueError('Geçersiz hedef ölçekleyici')

def register(mode, name, scope, endtrain, last, features, window, data=None, root=Path('models')):
    files, manifest = artifacts(mode, name, root)
    record = dict(version=combined(files), trained_at=datetime.now(timezone.utc).isoformat(),
                  training_end_year=endtrain, archive_end=str(last.date()), model=name,
                  mode=mode, scope=scope, features=features, schema_version=2,
                  files={p.name: sha256(p) for p in files}, window=int(window),
                  input_width=2 * len(features) + 1)
    if data is not None:
        record['training_data_sha256'] = sha256(data)
    manifest.write_text(json.dumps(record, indent=2), encoding='utf8')
    return verify(mode, name, root)
