#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Jade Coffee Analytics — setup script
# Usage:  bash setup.sh
# ──────────────────────────────────────────────────────────────────────────────

set -e

echo ""
echo "☕  Jade Coffee Analytics — Setup"
echo "────────────────────────────────────────"

# 1. Python check
if ! command -v python3 &>/dev/null; then
  echo "❌  python3 not found. Install Python 3.9+ and retry."
  exit 1
fi
# Prefer anaconda Python (has XGBoost + libomp bundled)
if [[ -x "/opt/anaconda3/bin/python" ]]; then
  PYTHON="/opt/anaconda3/bin/python"
else
  PYTHON=$(command -v python3)
fi
echo "✅  Python: $($PYTHON --version)"

# 2. Pip install
echo ""
echo "📦  Installing Python dependencies…"
$PYTHON -m pip install --upgrade pip -q
$PYTHON -m pip install -r requirements.txt

echo ""
echo "✅  Dependencies installed."

# 3. Ollama setup instructions
echo ""
echo "🤖  Ollama (for Ask Jade RAG feature)"
echo "────────────────────────────────────────"
if command -v ollama &>/dev/null; then
  echo "✅  Ollama is already installed."
  echo "   Run the following if you haven't pulled a model yet:"
  echo "   ollama pull llama3.2"
  echo "   ollama serve   (keep running in a separate terminal)"
else
  echo "   Ollama is NOT installed. To enable Ask Jade:"
  echo ""
  echo "   # Install Ollama (macOS)"
  echo "   brew install ollama"
  echo ""
  echo "   # Pull a lightweight model"
  echo "   ollama pull llama3.2"
  echo ""
  echo "   # Start Ollama server (separate terminal)"
  echo "   ollama serve"
  echo ""
  echo "   The dashboard works without Ollama — only Ask Jade will be disabled."
fi

# 4. Launch
echo ""
echo "────────────────────────────────────────"
echo "🚀  Starting Jade Coffee Analytics…"
echo "   Open http://localhost:8050 in your browser."
echo ""
$PYTHON app.py
