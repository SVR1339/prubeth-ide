# Contributing to PRUBETH IDE

Thank you for your interest in improving **PRUBETH IDE**!  
Official Project Portal: [**https://www.bsvr.work/#projects**](https://www.bsvr.work/#projects)

---

## 🚀 Development Workflow

### 1. Environment Setup
```powershell
# Clone the repository
git clone https://github.com/bsvr/so-naive.git
cd so-naive

# Create & activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
pip install pyinstaller pytest
```

### 2. Generate Brand Assets
```powershell
python generate_assets.py
```
This generates `assets/logo.svg`, `assets/logo.png`, and `assets/icon.ico`.

### 3. Running the Test Suite
Ensure all unit and integration tests pass before opening a Pull Request:
```powershell
pytest tests/ -v
```

### 4. Running the IDE
```powershell
python local_ai_studio_pro.py
```

### 5. Building the Windows Installer
```powershell
python build_installer.py
python build_setup_exe.py
```

---

## 📜 Pull Request Guidelines
- Follow PEP 8 guidelines for Python code.
- Ensure all QScintilla lexers and tool extraction engines remain regression-free.
- Add unit tests in `tests/test_studio.py` for new features or bug fixes.
- Reference relevant issues and include reproduction steps.
