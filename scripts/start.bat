@echo off
cd %~dp0\..
echo Starting Medical Classifier...
echo Loading models into memory, please wait...
call venv\Scripts\activate
python app.py
pause
