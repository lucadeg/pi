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

if ($Hydra) { $Model = "hydra-auto"; $Provider = "hydra-router" }
elseif ($Claude -or $Gemini -or $R1) {
    throw "Static provider/model aliases were removed because they could select stale or unavailable models. Use -Hydra for live routing or -Kimi for the verified Pi/Hydra bridge."
}
elseif ($Kimi) { $Model = "kimi-k3-moe"; $Provider = "kimi-k3" }

if (-not $Provider) {
    if ($Model -eq "hydra-auto") {
        $Provider = "hydra-router"
    } else {
        $Provider = "kimi-k3"
    }
}

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "  Pi Coding Agent - live provider routing" -ForegroundColor Green
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
