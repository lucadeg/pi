param(
    [string]$Model = "kimi-k3-moe",
    [string]$Provider = "",
    [switch]$Hydra,
    [switch]$Claude,
    [switch]$Gemini,
    [switch]$R1,
    [switch]$Kimi,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PI_CODING_AGENT_DIR = Join-Path $scriptDir ".pi\agent"
$env:PI_AGENT_DIR = Join-Path $scriptDir ".pi\agent"

if ($Hydra) { $Model = "auto"; $Provider = "hydra-router" }
elseif ($Claude) { $Model = "claude-sonnet-4-6"; $Provider = "hydra-router" }
elseif ($Gemini) { $Model = "gemini-2.5-flash"; $Provider = "hydra-router" }
elseif ($R1) { $Model = "deepseek-r1"; $Provider = "hydra-router" }
elseif ($Kimi) { $Model = "kimi-k3-moe"; $Provider = "kimi-k3" }

if (-not $Provider) {
    if ($Model -in @("auto", "gemini-2.5-flash", "gemini-3.5-flash", "claude-sonnet-4-6", "deepseek-r1", "llama-3.3-70b", "chatgpt")) {
        $Provider = "hydra-router"
    } else {
        $Provider = "kimi-k3"
    }
}

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "  Pi Coding Agent - Workflow 1-14 Standard Active" -ForegroundColor Green
Write-Host "  Provider: $Provider  |  Model: $Model" -ForegroundColor Yellow
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

if ($Provider -eq "kimi-k3") {
    $ensureScript = Join-Path $scriptDir "..\kimi-k3-in-c\ensure_kimi_service.py"
    if (Test-Path $ensureScript) {
        python $ensureScript
    }
}

$cliJs = Join-Path $scriptDir "packages\coding-agent\dist\cli.js"
if (Test-Path $cliJs) {
    node $cliJs --provider $Provider --model $Model @RemainingArgs
} else {
    $cliTs = Join-Path $scriptDir "packages\coding-agent\src\cli.ts"
    npx tsx $cliTs --provider $Provider --model $Model @RemainingArgs
}
exit $LASTEXITCODE
