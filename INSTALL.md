# Installation Guide: SUKHI IDE (v3.0.0 Horizon Edition)

Welcome to the official installation and developer onboarding guide for **SUKHI IDE — Horizon Edition v3.0.0** (formerly SO NAIVE IDE).  
Official Website & Downloads: [**https://www.bsvr.work/#projects**](https://www.bsvr.work/#projects)

---

## 🪟 Windows 10 / 11 Installation & Launch

### Method A: Standalone Setup Installer Wizard (Recommended for End Users)
1. Download **[`SukhiIDE-v3.0.0-Setup.exe`](https://github.com/bsvr/so-naive/releases/latest/download/SukhiIDE-v3.0.0-Setup.exe)** (or universal **`setup.exe`**).
2. Run the installer wizard. The wizard contains a verified, self-contained application payload.
3. Select your installation folder (defaults to `%LOCALAPPDATA%\Programs\SukhiIDE`).
4. Keep the boxes checked to create Desktop and Start Menu shortcuts.
5. Click **Install**. The wizard extracts the runtime payload, validates installation integrity, configures diagnostic launchers (`SukhiIDE.bat` and legacy `SoNaive.bat`), registers Windows Add/Remove Programs integration, and launches the IDE.

### Method B: Developer Quick Launch (Recommended for Developers)
If working directly inside the cloned or downloaded repository:
1. Double-click **`run_ide.bat`** (or **`run_local_ai_studio_pro.bat`**).
2. The launcher performs automated environment verification:
   - Checks for existing `.venv` or system Python 3.10+.
   - If missing dependencies (`PyQt5`, `QScintilla`, `requests`), automatically provisions a virtual environment and installs `requirements.txt`.
   - Starts **`local_ai_studio_pro.py`** with diagnostic error logging if unexpected crashes occur.

### Method C: Universal Portable ZIP (No Installation Required)
1. Download **[`SukhiIDE-v3.0.0-Universal-Portable.zip`](https://github.com/bsvr/so-naive/releases/latest/download/SukhiIDE-v3.0.0-Universal-Portable.zip)**.
2. Extract the archive to any folder (e.g., `C:\Tools\SukhiIDE`).
3. Double-click `run_ide.bat` (or `SukhiIDE.bat` / `SoNaive.bat`).

---

## 🐧 Ubuntu / Debian & Linux Installation

### Using the Native Shell Launcher (`run_ide.sh`):
```bash
# 1. Ensure execution permissions
chmod +x run_ide.sh

# 2. Run the launcher
./run_ide.sh
```
The Linux launcher automatically:
- Detects system `python3` (3.10+).
- Checks for and creates a `.venv` virtual environment if needed.
- Installs necessary pip dependencies (`PyQt5`, `QScintilla`, `requests`, `cryptography`).
- Launches SUKHI IDE with encrypted Fernet credential vault support.

---

## 📂 Repository Architecture & Modular Components

To maintain clear separation and prevent divergence across development tracks:

| File / Component | Role & Status | Description |
| :--- | :--- | :--- |
| **`local_ai_studio_pro.py`** | **PRIMARY IDE (Production)** | The official, full-featured v3.0.0 SUKHI IDE desktop application. |
| **`core/`** | **MODULAR SECURITY & AI ENGINE** | Decoupled core modules (`credentials`, `workspace`, `tool_gateway`, `model_registry`, `router`, `task_engine`, `plugin_engine`). |
| **`core/credentials.py`** | **ZERO-PLAINTEXT VAULT** | Windows DPAPI and Linux Fernet AES-GCM encryption with log secret scrubbing. |
| **`core/workspace.py`** | **WORKSPACE JAIL** | Canonical path enforcement preventing `../` traversal, symlink escapes, and providing atomic `.bak` saves. |
| **`core/tool_gateway.py`** | **TOOL SANDBOX** | Risk-classified execution gateway (`SAFE`, `MEDIUM`, `DANGEROUS`) with secret scrubbing. |
| **`core/router.py`** | **MODEL ROUTER** | Multi-model profile routing (`speed`, `complex_code`, `chat`, `cheap`, `agent`) with auto-failover. |
| **`run_ide.bat`** | **PRIMARY WINDOWS LAUNCHER** | User-friendly shortcut for developer launch with auto-bootstrap. |
| **`run_ide.sh`** | **LINUX LAUNCHER** | Cross-platform Linux bash launcher with automatic dependency bootstrap. |
| **`installer/setup_wizard.py`** | **INSTALLER ENGINE** | PyQt5 setup wizard with embedded payload extractor. |
| **`build_setup_exe.py`** | **INSTALLER BUILDER** | Packages `app_payload.zip` and builds standalone setup executable. |
| **`build_installer.py`** | **PACKAGING ENGINE** | Builds universal portable ZIP and PyInstaller onedir distribution. |
| **`requirements.txt`** | **CORE DEPENDENCIES** | Core runtime requirements (`PyQt5`, `QScintilla`, `requests`, `cryptography`). |
| **`tests/test_studio.py`** | **QUALITY TEST SUITE** | Comprehensive automated test suite (33/33 tests passing). |

---

## ⚡ Enabling Local CUDA GPU Acceleration (NVIDIA)

SUKHI IDE automatically connects to local Ollama GPU instances:

1. Install Ollama from [https://ollama.ai](https://ollama.ai).
2. Verify GPU detection:
   ```bash
   ollama run qwen2.5:1.5b "Hello"
   ```
3. Open SUKHI IDE. The bottom statusbar will display:
   `[GTX 1050 Ti · CUDA 12.6]` (or your installed NVIDIA GPU).
4. Run **Tools → Performance Radar & Matrix** to benchmark your live throughput!

---

## 🔑 Adding Cloud Reasoning Keys (Google Gemini, Anthropic, OpenAI, NavyAI)

1. Open **AI Agent → Settings & Models…** (or the **Universal Provider Hub**).
2. Paste your API keys for Google Gemini, Anthropic Claude, OpenAI, NavyAI, or Groq.
3. The IDE automatically encrypts the credentials using Windows DPAPI (or Fernet on Linux), scrubbing any plaintext from disk.
4. The IDE unlocks ultra-fast 1M-token context via low-latency SSE streaming and intelligent task-based routing.

---

For updates, documentation, and enterprise consulting, visit:  
[**https://www.bsvr.work/**](https://www.bsvr.work/)
