# PRUBETH — Universal Installation & Deployment Guide
### Release v1.91.0 · Cross-Platform Setup Manual

Official Website & Downloads: [**https://www.bsvr.work/#projects**](https://www.bsvr.work/#projects)  
GitHub Repository: [**https://github.com/SVR1339/prubeth-ide**](https://github.com/SVR1339/prubeth-ide)

---

## ⚡ Quick Start: One-Line Installers

### 🪟 Windows 10 & 11 (PowerShell)
Open PowerShell (Standard or Administrator) and run:
```powershell
irm https://raw.githubusercontent.com/SVR1339/prubeth-ide/master/install.ps1 | iex
```
*Automatically detects system configuration, checks or bootstraps Python 3.10+, provisions `.venv`, installs requirements, and sets up Desktop shortcuts.*

### 🐧 Linux (Ubuntu, Debian, Fedora, Arch) & 🍎 macOS
Open terminal and run:
```bash
curl -fsSL https://raw.githubusercontent.com/SVR1339/prubeth-ide/master/install.sh | bash
```
*Detects your Linux distribution or macOS environment, sets up an isolated virtual environment, configures Qt5 dependencies, and installs desktop application launcher entries.*

---

## 🪟 Windows Installation Methods

### Method 1: Standalone Single-Click Setup Wizard (Recommended for End Users)
1. Download or locate **`PrubethIDE-Setup.exe`** (or **`setup.exe`**).
2. Double-click the executable to launch the graphical Qt installation wizard.
3. Select installation path (defaults to `%LOCALAPPDATA%\Programs\PrubethIDE`).
4. Keep checked:
   - `[x] Create Desktop Shortcut`
   - `[x] Create Start Menu Shortcut`
5. Click **Install**. The wizard extracts all embedded binaries, configures launchers, and registers Windows Control Panel uninstall hooks.
6. The IDE launches immediately upon completion.

### Method 2: Local PowerShell Script
If you have cloned the repository locally:
```powershell
# Interactive run
powershell -ExecutionPolicy Bypass -File install.ps1

# Unattended / Silent run
powershell -ExecutionPolicy Bypass -File install.ps1 -Silent
```

### Method 3: Developer Source Launch
```cmd
# Double click the batch runner
run_local_ai_studio_pro.bat

# Or run directly via Python
.venv\Scripts\python.exe local_ai_studio_pro.py
```

---

## 🐧 Linux Installation Details

### Prerequisites by Distribution:

**Ubuntu / Debian / Linux Mint:**
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-pyqt5
```

**Fedora / RHEL / CentOS Stream:**
```bash
sudo dnf install -y python3 python3-virtualenv python3-pyqt5
```

**Arch Linux / Manjaro:**
```bash
sudo pacman -S python python-virtualenv python-pyqt5
```

### Installation Steps:
```bash
# 1. Clone repository
git clone https://github.com/SVR1339/prubeth-ide.git
cd prubeth-ide

# 2. Run automated installer
chmod +x install.sh
./install.sh

# 3. Launch the IDE
./run_prubeth.sh
```

---

## 🍎 macOS Installation (Apple Silicon & Intel)

### Prerequisites:
Install Python 3.10+ and Qt5 via Homebrew:
```bash
brew install python@3.12 pyqt@5
```

### Installation Steps:
```bash
git clone https://github.com/SVR1339/prubeth-ide.git
cd prubeth-ide
chmod +x install.sh
./install.sh
./run_prubeth.sh
```

---

## 🔍 Preflight Diagnostics & Verification

After installation, verify that all mandatory and optional subsystems are healthy:

```bash
# Windows
.venv\Scripts\python.exe local_ai_studio_pro.py --preflight-only

# Linux / macOS
.venv/bin/python local_ai_studio_pro.py --preflight-only
```

Sample expected output:
```text
============================================================
  PRUBETH IDE v3.0.0 PREFLIGHT DIAGNOSTICS REPORT
============================================================
Overall Status: PASS
[PASS] [INTEGRITY] Application Entry Point: Found primary entry point: local_ai_studio_pro.py
[PASS] [INTEGRITY] User Data Directory Writable: Verified write access
[PASS] [RUNTIME] Python Version: Python 3.12.2 is supported
[PASS] [RUNTIME] Mandatory: PyQt5: Loaded PyQt5 GUI core framework
[PASS] [RUNTIME] Mandatory: requests: Loaded HTTP communication client
[PASS] [RUNTIME] Mandatory: sqlite3: Loaded Task and checkpoint database engine
[PASS] [RUNTIME] Mandatory: json: Loaded Configuration serialization
[PASS] [RUNTIME] Optional: PyQt5.Qsci: QScintilla advanced syntax engine
[PASS] [RUNTIME] Optional: torch: PyTorch local CUDA tensor inference
[PASS] [CONFIGURATION] Configuration File Integrity: Settings JSON validated
[PASS] [ENVIRONMENT] Disk Free Space: 80+ GB storage free
============================================================
```

---

## 🧪 Running the Verification Test Suite

PRUBETH IDE ships with a complete automated test suite ensuring zero regressions:

```bash
# Windows
.venv\Scripts\python.exe -m pytest tests/ -v

# Linux / macOS
.venv/bin/python -m pytest tests/ -v
```

All **254 automated tests** will execute and report 100% pass status across reliability, concurrency, agent loops, security boundaries, and hardware autotuning.

---

<div align="center">
  <p>© 2025–2026 BSVR Technologies. Engineered for next-generation developer flow.</p>
  <p><a href="https://www.bsvr.work/">Official Website</a> · <a href="https://github.com/SVR1339/prubeth-ide">GitHub Repository</a></p>
</div>
