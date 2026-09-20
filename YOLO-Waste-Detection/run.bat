@echo off
REM Runs waste detection.
REM   run.bat                        -> webcam
REM   run.bat --source video.mp4      -> video file
REM   run.bat --source image.jpg      -> image file
REM   run.bat --source image.jpg --output out.jpg
python detect_camera.py %*
pause
