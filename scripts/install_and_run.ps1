$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$EnvFile = Join-Path $Backend ".env"
$EnvExample = Join-Path $Backend ".env.example"
$ProjectCondaPython = Join-Path $Root ".conda\python.exe"
$SiblingDemoCondaPython = Join-Path (Split-Path -Parent $Root) "RJB_demo\.conda\python.exe"

function Write-Step($Message) {
  Write-Host ""
  Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-Command($Name, $InstallHint) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Command not found: $Name. $InstallHint"
  }
}

Write-Host "EduMate one-click install and run" -ForegroundColor Green
Write-Host "Project root: $Root"

Write-Step "Checking Node.js and npm"
Assert-Command "node" "Please install Node.js 20 LTS: https://nodejs.org/"
Assert-Command "npm" "npm is installed with Node.js."
node --version
npm --version

Write-Step "Selecting Python runtime"
if (Test-Path $ProjectCondaPython) {
  $Python = $ProjectCondaPython
} elseif (Test-Path $SiblingDemoCondaPython) {
  $Python = $SiblingDemoCondaPython
} elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
  $Python = "python"
} else {
  throw "Python not found. Please install Python 3.11 or provide .conda\python.exe in the project root."
}
Write-Host "Python: $Python"
& $Python --version

Write-Step "Preparing backend environment file"
if (-not (Test-Path $EnvFile)) {
  if (-not (Test-Path $EnvExample)) {
    throw "Missing backend\.env.example."
  }
  Copy-Item -LiteralPath $EnvExample -Destination $EnvFile
  $envText = Get-Content -LiteralPath $EnvFile -Raw
  $envText = $envText -replace 'LLM_PROVIDER=deepseek', 'LLM_PROVIDER=mock'
  $envText = $envText -replace 'LLM_PROVIDER=auto', 'LLM_PROVIDER=mock'
  $envText = $envText -replace 'GRAPH_BACKEND=auto', 'GRAPH_BACKEND=memory'
  $envText = $envText -replace 'GRAPH_BACKEND=neo4j', 'GRAPH_BACKEND=memory'
  Set-Content -LiteralPath $EnvFile -Value $envText -Encoding UTF8
  Write-Host "Created backend\.env with mock LLM and memory graph for first-run demo." -ForegroundColor Yellow
  Write-Host "To use real DeepSeek or iFlytek TTS, edit backend\.env and restart." -ForegroundColor Yellow
} else {
  Write-Host "Found backend\.env. Existing configuration will be used."
}

Write-Step "Installing backend dependencies"
Set-Location $Backend
& $Python -m pip install -r requirements.txt

Write-Step "Installing frontend dependencies"
Set-Location $Frontend
if (-not (Test-Path "node_modules")) {
  npm install
} else {
  Write-Host "Found frontend\node_modules. Skipping npm install."
}

Write-Step "Starting backend and frontend"
$BackendScript = Join-Path $PSScriptRoot "start_backend.ps1"
$FrontendScript = Join-Path $PSScriptRoot "start_frontend.ps1"

Start-Process powershell.exe -ArgumentList @(
  "-NoExit",
  "-ExecutionPolicy", "Bypass",
  "-File", "`"$BackendScript`""
) -WorkingDirectory $Root -WindowStyle Normal

Start-Sleep -Seconds 3

Start-Process powershell.exe -ArgumentList @(
  "-NoExit",
  "-ExecutionPolicy", "Bypass",
  "-File", "`"$FrontendScript`""
) -WorkingDirectory $Root -WindowStyle Normal

Write-Host ""
Write-Host "Startup commands were launched." -ForegroundColor Green
Write-Host "Wait until the frontend window shows VITE ready, then open:" -ForegroundColor Green
Write-Host "http://127.0.0.1:5173/#/portal" -ForegroundColor Green
Write-Host ""
Write-Host "If ports are already in use, close old uvicorn/vite processes and run again."
