@echo off
echo Installing dependencies...
pip install -r requirements
if %errorlevel% neq 0 (
    echo Installation failed.
    pause
    exit /b %errorlevel%
)
echo Done.
pause
