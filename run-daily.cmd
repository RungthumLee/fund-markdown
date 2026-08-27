@echo off
REM Scheduled entry point for the Fund Knowledge daily run.
REM Register with:
REM   schtasks /Create /TN "FundKnowledge Daily" /SC DAILY /ST 07:30 ^
REM     /TR "d:\Website\Fund-knowledge\run-daily.cmd" /RL LIMITED /F
REM
REM The exit code of daily.py is passed straight through, so Task Scheduler
REM shows the task as failed when a stage breaks.

cd /d "%~dp0"

REM Thai stage names would otherwise land in the log as cp874 mojibake
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

python daily.py %*
exit /b %ERRORLEVEL%
