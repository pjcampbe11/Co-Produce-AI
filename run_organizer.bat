@echo off
REM Organize F:\Sound Bank - dry run first, then real run, then AI tags.
cd /d %~dp0
if not exist .venv (python -m venv .venv && .venv\Scripts\pip install -r requirements.txt)
.venv\Scripts\python scripts\organize_soundbank.py --input "F:\Sound Bank" --output "F:\Sound Bank Organized" --dry-run
echo.
echo Dry run done - review "F:\Sound Bank Organized\review.csv".
set /p GO="Type YES to run for real (copies files): "
if /i "%GO%"=="YES" .venv\Scripts\python scripts\organize_soundbank.py --input "F:\Sound Bank" --output "F:\Sound Bank Organized" --resume
