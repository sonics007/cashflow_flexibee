@echo off
cd /d "%~dp0"
echo Starting Cashflow Dashboard...

IF EXIST venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) ELSE (
    echo Virtual environment not found, using global Python...
)

set FLASK_APP=app.py
set FLASK_ENV=development
python app.py
pause
