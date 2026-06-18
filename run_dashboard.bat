@echo off
REM Launch the toolkit dashboard in your browser.
cd /d %~dp0
if not exist .venv (python -m venv .venv && .venv\Scripts\pip install -r requirements.txt)
.venv\Scripts\pip install -q gradio
.venv\Scripts\python dashboard.py
