@echo off
REM Startup script for Commercial Real Estate Scraper Web App (Windows)

echo ========================================
echo Starting Web App...
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Create output directory
if not exist "output" mkdir output

REM Start the app
echo.
echo ========================================
echo Starting server...
echo ========================================
echo.

python app.py

pause
