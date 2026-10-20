@echo off
cd /d "%~dp0"
python build_library.py
start chrome "%~dp0library.html"
