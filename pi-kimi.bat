@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PI_CODING_AGENT_DIR=%SCRIPT_DIR%.pi\agent"
set "PI_AGENT_DIR=%SCRIPT_DIR%.pi\agent"
set "KIMI_DIR=%SCRIPT_DIR%..\kimi-k3-in-c"

echo ================================================================================
echo  [PI AGENT] Standalone Sovereign Runner with KIMI K3 IN C (Local MoE)
echo ================================================================================
echo  Active Local Endpoint: http://127.0.0.1:8095 (Kimi K3)
echo --------------------------------------------------------------------------------

:: Ensure Kimi K3 is running
if exist "%KIMI_DIR%\ensure_kimi_service.py" (
    where python >nul 2>nul
    if not errorlevel 1 (
        python "%KIMI_DIR%\ensure_kimi_service.py"
    )
)

set "CLI_DIST=%SCRIPT_DIR%packages\coding-agent\dist\cli.js"
set "CLI_TSX=%SCRIPT_DIR%packages\coding-agent\src\cli.ts"

if exist "%CLI_DIST%" (
    if "%~1"=="" (
        node "%CLI_DIST%" --provider kimi-k3 --model kimi-k3-moe
    ) else (
        node "%CLI_DIST%" --provider kimi-k3 --model kimi-k3-moe %*
    )
) else (
    if "%~1"=="" (
        "%SCRIPT_DIR%node_modules\.bin\tsx.cmd" "%CLI_TSX%" --provider kimi-k3 --model kimi-k3-moe
    ) else (
        "%SCRIPT_DIR%node_modules\.bin\tsx.cmd" "%CLI_TSX%" --provider kimi-k3 --model kimi-k3-moe %*
    )
)
