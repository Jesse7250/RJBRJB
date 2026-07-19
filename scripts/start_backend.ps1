$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$ProjectCondaPython = Join-Path $Root ".conda\python.exe"
$SiblingDemoCondaPython = Join-Path (Split-Path -Parent $Root) "RJB_demo\.conda\python.exe"

Set-Location $Backend

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created backend\.env. Please fill API keys and run this script again." -ForegroundColor Yellow
  exit 1
}

if (Test-Path $ProjectCondaPython) {
  $Python = $ProjectCondaPython
} elseif (Test-Path $SiblingDemoCondaPython) {
  $Python = $SiblingDemoCondaPython
} else {
  $Python = "python"
}

& $Python -m pip install -r requirements.txt
& $Python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
