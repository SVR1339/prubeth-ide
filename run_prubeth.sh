#!/usr/bin/env bash
# ==============================================================================
# PRUBETH — Universal Linux & macOS Runtime Launcher
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# 1. Resolve Python 3 executable
if [ -d "${SCRIPT_DIR}/.venv" ]; then
    PYTHON_BIN="${SCRIPT_DIR}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
else
    echo "[-] Error: Python 3 not found. Please run ./install.sh first."
    exit 1
fi

# 2. Launch PRUBETH
echo "[+] Starting PRUBETH Autonomous Developer Platform..."
exec "${PYTHON_BIN}" "${SCRIPT_DIR}/local_ai_studio_pro.py" "$@"
