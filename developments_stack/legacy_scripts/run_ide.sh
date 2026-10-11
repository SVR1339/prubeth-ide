#!/usr/bin/env bash
# PRUBETH IDE — Horizon Edition v3.0.0
# Linux / Ubuntu Launcher & Environment Bootstrapper
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==============================================================================="
echo "  PRUBETH IDE — Horizon Edition (v3.0.0)"
echo "  AI-Native Developer Environment for Linux & Windows"
echo "==============================================================================="

# 1. Detect Python binary
if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo "[ERROR] Python 3 was not detected on your system PATH."
    echo "Please install Python 3.10+ via:"
    echo "  sudo apt update && sudo apt install -y python3 python3-venv python3-pip python3-pyqt5"
    exit 1
fi

# 2. Check dependencies
if ! "$PYTHON_BIN" -c "import PyQt5, requests" &>/dev/null; then
    echo "[*] Setting up local .venv with required packages..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        .venv/bin/pip install -r requirements.txt
    fi
    PYTHON_BIN=".venv/bin/python"
fi

echo "[*] Launching PRUBETH IDE via $PYTHON_BIN..."
exec "$PYTHON_BIN" local_ai_studio_pro.py "$@"
