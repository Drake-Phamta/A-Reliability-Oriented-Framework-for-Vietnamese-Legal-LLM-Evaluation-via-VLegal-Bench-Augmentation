#!/bin/bash
set -e

echo "========================================"
echo "  VLegal-Bench Setup (Linux/Mac)"
echo "========================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Install Python 3.10+ first."
    exit 1
fi
echo "[OK] Python3 found: $(python3 --version)"

# Create venv
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi
echo "[OK] Virtual environment ready"

# Activate
source venv/bin/activate

# Install dependencies
echo "[INFO] Installing dependencies..."
pip install openai tiktoken rouge-score nltk python-dotenv tqdm matplotlib -q
echo "[OK] Core dependencies installed"

# Optional: fine-tune
read -p "Install fine-tune dependencies? (y/N): " INSTALL_FT
if [[ "$INSTALL_FT" =~ ^[Yy]$ ]]; then
    echo "[INFO] Installing fine-tune dependencies..."
    pip install torch transformers peft trl datasets -q
    echo "[OK] Fine-tune dependencies installed"
fi

# Setup .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[INFO] Created .env from template - EDIT IT with your API keys!"
fi

# NLTK data
python3 -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)" 2>/dev/null

# Verify
echo ""
echo "========================================"
echo "  Verifying setup..."
echo "========================================"
python3 -c "import openai; import tiktoken; import rouge_score; import tqdm; print('[OK] All core packages loaded')"
python3 -c "from src.evaluation import Metrics; print('[OK] evaluation.py loaded')"
python3 -c "from src.reliability_metrics import ReliabilityMetrics; print('[OK] reliability_metrics.py loaded')"

echo ""
echo "========================================"
echo "  Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Read TEAM_GUIDE.md for your tasks"
echo "  3. Run: source venv/bin/activate && python tools/run_experiments.py --help"
