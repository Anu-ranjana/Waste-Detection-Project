@echo off
setlocal

rem DeepFace's logger prints emoji characters, which crash on Windows
rem consoles using the default cp1252 codepage. Force UTF-8 I/O.
set PYTHONIOENCODING=utf-8

cd /d "%~dp0webapp"
python app.py

endlocal
