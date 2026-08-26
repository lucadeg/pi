@echo off
setlocal enabledelayedexpansion

REM =========================================================================
REM  Pi Coding Agent — Unified Master Launcher (Kimi K3 + Hydra Router)
REM  Enforces Workflow 1-14, Anti-Slop, and Dynamic Model Matrix
REM =========================================================================

set "SCRIPT_DIR=%~dp0"
set "PI_CODING_AGENT_DIR=%SCRIPT_DIR%.pi\agent"
set "PI_AGENT_DIR=%SCRIPT_DIR%.pi\agent"
set "CLI_JS=%SCRIPT_DIR%packages\coding-agent\dist\cli.js"

REM Default to local Kimi K3 MoE if no model provided
set "SELECTED_PROVIDER=kimi-k3"
set "SELECTED_MODEL=kimi-k3-moe"
set "EXTRA_ARGS="

:parse_args
if "%~1"=="" goto run_pi
if /i "%~1"=="--model" (
    set "SELECTED_MODEL=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="-m" (
    set "SELECTED_MODEL=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--provider" (
    set "SELECTED_PROVIDER=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--hydra" (
    set "SELECTED_PROVIDER=hydra-router"
    set "SELECTED_MODEL=auto"
    shift
    goto parse_args
)
if /i "%~1"=="--claude" (
    set "SELECTED_PROVIDER=hydra-router"
    set "SELECTED_MODEL=claude-sonnet-4-6"
    shift
    goto parse_args
)
if /i "%~1"=="--gemini" (
    set "SELECTED_PROVIDER=hydra-router"
    set "SELECTED_MODEL=gemini-2.5-flash"
    shift
    goto parse_args
)
if /i "%~1"=="--r1" (
    set "SELECTED_PROVIDER=hydra-router"
    set "SELECTED_MODEL=deepseek-r1"
    shift
    goto parse_args
)
if /i "%~1"=="--kimi" (
    set "SELECTED_PROVIDER=kimi-k3"
    set "SELECTED_MODEL=kimi-k3-moe"
    shift
    goto parse_args
)
set "EXTRA_ARGS=!EXTRA_ARGS! %1"
shift
goto parse_args

:run_pi
REM Auto-detect provider based on model name
if /i "%SELECTED_MODEL%"=="auto" set "SELECTED_PROVIDER=hydra-router"
if /i "%SELECTED_MODEL%"=="gemini-2.5-flash" set "SELECTED_PROVIDER=hydra-router"
if /i "%SELECTED_MODEL%"=="gemini-3.5-flash" set "SELECTED_PROVIDER=hydra-router"
if /i "%SELECTED_MODEL%"=="claude-sonnet-4-6" set "SELECTED_PROVIDER=hydra-router"
if /i "%SELECTED_MODEL%"=="deepseek-r1" set "SELECTED_PROVIDER=hydra-router"
if /i "%SELECTED_MODEL%"=="llama-3.3-70b" set "SELECTED_PROVIDER=hydra-router"
if /i "%SELECTED_MODEL%"=="chatgpt" set "SELECTED_PROVIDER=hydra-router"
if /i "%SELECTED_MODEL%"=="kimi-k3-moe" set "SELECTED_PROVIDER=kimi-k3"
if /i "%SELECTED_MODEL%"=="qwen2.5-coder:3b" set "SELECTED_PROVIDER=kimi-k3"

echo.
echo =========================================================================
echo   Pi Coding Agent - Workflow 1-14 Standard Active
echo   Provider: !SELECTED_PROVIDER!  ^|  Model: !SELECTED_MODEL!
echo =========================================================================
echo.

REM Auto ensure backend is active
if /i "!SELECTED_PROVIDER!"=="kimi-k3" (
    echo [INFO] Ensuring Kimi K3 MoE C-Engine (port 8095) is running...
    python "%SCRIPT_DIR%..\kimi-k3-in-c\ensure_kimi_service.py"
)

if /i "!SELECTED_PROVIDER!"=="hydra-router" (
    echo [INFO] Target Hydra Router at http://127.0.0.1:8090/v1
)

if exist "%CLI_JS%" (
    node "%CLI_JS%" --provider "!SELECTED_PROVIDER!" --model "!SELECTED_MODEL!" !EXTRA_ARGS!
) else (
    npx tsx "%SCRIPT_DIR%packages\coding-agent\src\cli.ts" --provider "!SELECTED_PROVIDER!" --model "!SELECTED_MODEL!" !EXTRA_ARGS!
)

exit /b %ERRORLEVEL%
