@echo off
chcp 65001 >nul
echo ========================================
echo   VLegal-Bench Setup (Windows)
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ first.
    pause
    exit /b 1
)
echo [OK] Python found

:: Create venv
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)
echo [OK] Virtual environment ready

:: Activate
call venv\Scripts\activate.bat

:: Install dependencies
echo [INFO] Installing dependencies...
pip install openai tiktoken rouge-score nltk python-dotenv tqdm matplotlib -q
echo [OK] Core dependencies installed

:: Optional: fine-tune dependencies
set /p INSTALL_FT="Install fine-tune dependencies? (y/N): "
if /i "%INSTALL_FT%"=="y" (
    echo [INFO] Installing fine-tune dependencies...
    pip install torch transformers peft trl datasets -q
    echo [OK] Fine-tune dependencies installed
)

:: Setup .env
if not exist ".env" (
    copy .env.example .env >nul
    echo [INFO] Created .env from template - EDIT IT with your API keys!
)

:: Download NLTK data
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)" 2>nul

:: Verify
echo.
echo ========================================
echo   Verifying setup...
echo ========================================
python -c "import openai; import tiktoken; import rouge_score; import tqdm; print('[OK] All core packages loaded')" 2>&1
python -c "from src.evaluation import Metrics; print('[OK] evaluation.py loaded')" 2>&1
python -c "from src.reliability_metrics import ReliabilityMetrics; print('[OK] reliability_metrics.py loaded')" 2>&1

echo.
echo ========================================
echo   Setup complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit .env with your API keys
echo   2. Read TEAM_GUIDE.md for your tasks
echo   3. Run: venv\Scripts\activate ^&^& python tools/run_experiments.py --help
echo.
pause
