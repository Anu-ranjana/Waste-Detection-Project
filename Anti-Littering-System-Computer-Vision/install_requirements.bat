@echo off
setlocal

echo ============================================
echo Anti-Littering System - Dependency Installer
echo ============================================

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] python was not found on PATH. Install Python or activate your conda/venv environment first.
    exit /b 1
)

echo.
echo [1/2] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    exit /b 1
)

echo.
echo [2/2] Installing requirements from requirements.txt...
python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo [ERROR] Failed to install one or more requirements.
    exit /b 1
)

echo.
echo [3/3] Checking MoveNet model file...
if not exist "%~dp0MoveNet\tflite\lite-model_movenet_singlepose_lightning_tflite_float16_4.tflite" (
    echo MoveNet model not found. Downloading...
    if not exist "%~dp0MoveNet\tflite" mkdir "%~dp0MoveNet\tflite"
    curl -L -o "%~dp0MoveNet\tflite\lite-model_movenet_singlepose_lightning_tflite_float16_4.tflite" "https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/tflite/float16/4?lite-format=tflite"
    if errorlevel 1 (
        echo [ERROR] Failed to download MoveNet model. Download it manually from:
        echo   https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/tflite/float16/4
        echo and place it at MoveNet\tflite\lite-model_movenet_singlepose_lightning_tflite_float16_4.tflite
        exit /b 1
    )
) else (
    echo MoveNet model already present.
)

echo.
echo ============================================
echo All dependencies installed successfully.
echo Note: DeepFace prints emoji log messages that can crash
echo on Windows consoles using non-UTF8 codepages. Use run.bat
echo to launch the app with UTF-8 I/O enabled.
echo ============================================
endlocal
