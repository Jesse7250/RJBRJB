$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Frontend = Join-Path $Root "frontend"

Set-Location $Frontend

if (-not (Test-Path "node_modules")) {
  npm install
}

npm run dev -- --host 127.0.0.1 --port 5173

