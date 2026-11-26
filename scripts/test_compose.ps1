# Run only against a newly approved local test project, never a production volume.
param([switch]$Run)
$ErrorActionPreference = "Stop"
if (-not $Run) { Write-Host "Bu kontrol yeni lst-validation Compose projesini oluşturur. Onay sonrası: .\scripts\test_compose.ps1 -Run"; exit 0 }
if (-not $env:LST_DB_PASSWORD) { throw "LST_DB_PASSWORD ortam değişkenini kendin ayarlamalısın." }
Set-Location (Split-Path $PSScriptRoot -Parent)
docker compose -p lst-validation up --build -d
if ($LASTEXITCODE -ne 0) { throw "Compose başlatılamadı" }
$Ready = $false
for ($Try=0; $Try -lt 60; $Try++) {
    try { $Health = Invoke-RestMethod http://localhost:5274/health; if ($Health.status -eq "ready") { $Ready=$true; break } } catch { }
    Start-Sleep -Seconds 2
}
if (-not $Ready) { throw "API hazır olmadı; docker compose -p lst-validation logs ile incele" }
$Before = Invoke-RestMethod http://localhost:5274/api/iller
if ($Before.Count -ne 81) { throw "81 il bekleniyordu" }
docker compose -p lst-validation restart
if ($LASTEXITCODE -ne 0) { throw "Yeniden başlatma başarısız" }
$Ready=$false
for ($Try=0; $Try -lt 60; $Try++) {
    try { $After=Invoke-RestMethod http://localhost:5274/api/iller; if ($After.Count -eq 81) { $Ready=$true; break } } catch { }
    Start-Sleep -Seconds 2
}
if (-not $Ready) { throw "Yeniden başlatma sonrası veri doğrulanamadı" }
Write-Host "İlk açılış ve yeniden başlatma doğrulandı. Volume silinmedi."
