@echo off
rem Entry point for the development commands in scripts\dev.ps1 (works with the default execution policy).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\dev.ps1" %*
exit /b %ERRORLEVEL%
