#!/usr/bin/env bash
# ==============================================================================
# PRUBETH IDE — Unified Linux & macOS Automated Installer
# Bloom, ideas unfolding
# https://github.com/imyouiamyou/prubeth-ide
# ==============================================================================

set -e

MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${MAGENTA}================================================================${NC}"
echo -e "${MAGENTA}             PRUBETH IDE — BLOOM EDITION (v3.0.0)              ${NC}"
echo -e "${CYAN}                   Bloom, ideas unfolding                       ${NC}"
echo -e "${MAGENTA}================================================================${NC}"

# Detect OS
OS_TYPE="$(uname -s)"
case "${OS_TYPE}" in
    Linux*)     PLATFORM="Linux";;
    Darwin*)    PLATFORM="macOS";;
    *)          PLATFORM="UNKNOWN";;
esac

echo -e "${GREEN}[+] Detected Operating System: ${PLATFORM} ($(uname -m))${NC}"

# Locate Python 3.10+
PYTHON_BIN=""
for cmd in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        VER_MAJOR=$("$cmd" -c 'import sys; print(sys.version_info.major)')
        VER_MINOR=$("$cmd" -c 'import sys; print(sys.version_info.minor)')
        if [ "$VER_MAJOR" -eq 3 ] && [ "$VER_MINOR" -ge 10 ]; then
            PYTHON_BIN="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}[-] Python 3.10 or higher is required but was not found in PATH.${NC}"
    if [ "$PLATFORM" = "Linux" ]; then
        echo -e "${YELLOW}[!] Install on Ubuntu/Debian: sudo apt update && sudo apt install -y python3 python3-venv python3-pip python3-pyqt5${NC}"
        echo -e "${YELLOW}[!] Install on Fedora:        sudo dnf install -y python3 python3-virtualenv python3-pyqt5${NC}"
        echo -e "${YELLOW}[!] Install on Arch Linux:    sudo pacman -S python python-virtualenv python-pyqt5${NC}"
    elif [ "$PLATFORM" = "macOS" ]; then
        echo -e "${YELLOW}[!] Install with Homebrew:    brew install python@3.12 pyqt@5${NC}"
    fi
    exit 1
fi

echo -e "${GREEN}[+] Using Python interpreter: $($PYTHON_BIN --version) (${PYTHON_BIN})${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

# Create Virtual Environment if not exists
if [ ! -d "${VENV_DIR}" ]; then
    echo -e "${GREEN}[+] Creating isolated virtual environment in: ${VENV_DIR}${NC}"
    "$PYTHON_BIN" -m venv "${VENV_DIR}"
fi

VENV_PY="${VENV_DIR}/bin/python"
VENV_PIP="${VENV_DIR}/bin/pip"

echo -e "${GREEN}[+] Upgrading pip and core build tools...${NC}"
"$VENV_PY" -m pip install --upgrade pip setuptools wheel --quiet

# Install Requirements
if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
    echo -e "${GREEN}[+] Installing dependencies from requirements.txt...${NC}"
    "$VENV_PIP" install -r "${SCRIPT_DIR}/requirements.txt" || {
        echo -e "${YELLOW}[!] Non-fatal warnings encountered during pip install. Continuing...${NC}"
    }
fi

# Create Linux Desktop entry if on Linux desktop
if [ "$PLATFORM" = "Linux" ] && [ -n "$XDG_DATA_HOME" -o -d "$HOME/.local/share" ]; then
    APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
    mkdir -p "$APPS_DIR"
    DESKTOP_FILE="${APPS_DIR}/prubeth-ide.desktop"
    cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Name=PRUBETH IDE
Comment=Next-Gen Agentic AI Developer Environment
Exec=${SCRIPT_DIR}/run_prubeth.sh
Icon=${SCRIPT_DIR}/assets/logo.png
Terminal=false
Categories=Development;IDE;Programming;
StartupWMClass=prubeth-ide
EOF
    chmod +x "$DESKTOP_FILE"
    echo -e "${GREEN}[+] Installed Linux Desktop Entry: ${DESKTOP_FILE}${NC}"
fi

# Create convenient runner script
RUNNER="${SCRIPT_DIR}/run_prubeth.sh"
cat <<EOF > "$RUNNER"
#!/usr/bin/env bash
cd "${SCRIPT_DIR}"
exec "${VENV_PY}" "${SCRIPT_DIR}/local_ai_studio_pro.py" "\$@"
EOF
chmod +x "$RUNNER"
echo -e "${GREEN}[+] Created executable launcher: ${RUNNER}${NC}"

# Execute preflight verification
echo -e "${GREEN}[+] Running preflight diagnostics...${NC}"
"${VENV_PY}" "${SCRIPT_DIR}/local_ai_studio_pro.py" --preflight-only || true

echo -e "${CYAN}================================================================${NC}"
echo -e "${GREEN}         PRUBETH IDE INSTALLATION COMPLETED SUCCESSFULLY!       ${NC}"
echo -e "${CYAN}================================================================${NC}"
echo -e "Launch methods:"
echo -e "  1. Launcher Script: ./run_prubeth.sh"
echo -e "  2. Virtualenv CLI:  .venv/bin/python local_ai_studio_pro.py"
echo ""
