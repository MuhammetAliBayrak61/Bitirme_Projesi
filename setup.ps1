$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Python 3.12 ortamı oluşturulamadı." }
& .\.venv\Scripts\python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Bağımlılıklar kurulamadı." }
$env:KERAS_BACKEND = "jax"
$LogDir = Join-Path "results/local-validation" (Get-Date -Format "yyyyMMdd-HHmmss")
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
& .\.venv\Scripts\python scripts/check_environment.py --report "$LogDir/environment.json"
if ($LASTEXITCODE -ne 0) { throw "Sürüm kontrolü başarısız." }
$TestProcess = Start-Process -FilePath "$PSScriptRoot\.venv\Scripts\python.exe" -ArgumentList @("-m", "unittest", "discover", "-s", "tests", "-v") -Wait -PassThru -NoNewWindow -RedirectStandardOutput "$LogDir/tests.stdout.txt" -RedirectStandardError "$LogDir/tests.stderr.txt"
Get-Content "$LogDir/tests.stdout.txt", "$LogDir/tests.stderr.txt"
if ($TestProcess.ExitCode -ne 0) { throw "Testler başarısız. Kayıt: $LogDir" }
Write-Host "Kurulum ve test kaydı: $LogDir"
