@echo off
REM AI File Classifier - Setup Script for Windows
REM This script sets up the virtual environment and installs dependencies

echo ==========================================
echo AI File Classifier - Setup
echo ==========================================
echo.

REM Check Python installation
echo Checking Python version...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://python.org
    pause
    exit /b 1
)

python --version
echo.

REM Check Python version is 3.10 or higher
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python 3.10 or higher is required
    echo Please upgrade Python from https://python.org
    pause
    exit /b 1
)

echo [OK] Python version check passed
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist venv\ (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    echo [OK] Virtual environment created
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded
echo.

REM Install package
echo Installing AI File Classifier...
pip install -e . --quiet
if %ERRORLEVEL% NEQ 0 (
    echo Error: Installation failed
    pause
    exit /b 1
)
echo [OK] Package installed
echo.

REM Verify installation
echo Verifying installation...
python -m src.main --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Installation verified
) else (
    echo Warning: Could not verify installation
)
echo.

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env >nul
    echo [OK] .env file created
    echo   Please edit .env and add your API key if using OpenAI
) else (
    echo .env file already exists
)
echo.

echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo To activate the virtual environment in the future, run:
echo   venv\Scripts\activate
echo.
echo To start using the classifier, run:
echo   python -m src.main classify ^<source^> ^<destination^>
echo.
echo For help, run:
echo   python -m src.main classify --help
echo.
pause
