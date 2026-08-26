$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Set local agent directory for Pi to read models.json
$env:PI_CODING_AGENT_DIR = Join-Path $scriptDir ".pi\agent"
$env:PI_AGENT_DIR = Join-Path $scriptDir ".pi\agent"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " [PI AGENT] Standalone Runner coupled with KIMI K3 IN C (Local MoE)" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " Active Backend: http://127.0.0.1:8095 (Kimi K3 Local Inference Engine)" -ForegroundColor Yellow
Write-Host " Model: kimi-k3-moe | Context: 128K | Cost: $0.00 (Zero API Cost)" -ForegroundColor Gray
Write-Host "--------------------------------------------------------------------------------`n"

# Ensure Kimi K3 service is online
$kimiEnsureScript = Join-Path $scriptDir "..\kimi-k3-in-c\ensure_kimi_service.py"
if (Test-Path -LiteralPath $kimiEnsureScript) {
    try {
        & python $kimiEnsureScript
    } catch {
        Write-Warning "Could not run ensure_kimi_service.py: $_"
    }
}

$cliDist = Join-Path $scriptDir "packages\coding-agent\dist\cli.js"
$cliTsx = Join-Path $scriptDir "packages\coding-agent\src\cli.ts"
$tsxBin = Join-Path $scriptDir "node_modules\.bin\tsx.cmd"

if (Test-Path -LiteralPath $cliDist) {
    if ($args.Count -eq 0) {
        & node $cliDist --provider kimi-k3 --model kimi-k3-moe
    } else {
        & node $cliDist --provider kimi-k3 --model kimi-k3-moe @args
    }
} elseif (Test-Path -LiteralPath $tsxBin) {
    if ($args.Count -eq 0) {
        & $tsxBin $cliTsx --provider kimi-k3 --model kimi-k3-moe
    } else {
        & $tsxBin $cliTsx --provider kimi-k3 --model kimi-k3-moe @args
    }
} else {
    throw "Neither dist/cli.js nor tsx found. Run 'npm run build' or 'npm install' in $scriptDir."
}
