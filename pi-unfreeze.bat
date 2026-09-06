@echo off
title Pi Coding Agent (No-Freeze)
echo ================================================================================
echo  [PI AGENT] Unfreeze Console Launcher (QuickEdit Disabled)
echo ================================================================================
echo  NOTA: Se il terminale mostra 'Seleziona' nel titolo della finestra, premi [ESC]
echo  per sbloccare la digitazione.
echo --------------------------------------------------------------------------------

:: Try launching in Windows Terminal if available for smooth input
where wt.exe >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Avvio in Windows Terminal...
    start "" wt.exe cmd /k "cd /d c:\Users\Deglu\.hermes && call tools\pi\pi.bat %*"
    exit /b 0
)

:: Fallback direct launch
cd /d "c:\Users\Deglu\.hermes"
call tools\pi\pi.bat %*
