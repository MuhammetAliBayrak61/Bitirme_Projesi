$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Python 3.12 ortamı oluşturulamadı." }
& .\.venv\Scripts\python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Bağımlılıklar kurulamadı." }
$env:KERAS_BACKEND = "jax"
& .\.venv\Scripts\python scripts/check_environment.py
if ($LASTEXITCODE -ne 0) { throw "Sürüm kontrolü başarısız." }
& .\.venv\Scripts\python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Testler başarısız." }
