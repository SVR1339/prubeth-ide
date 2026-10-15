import os
import re
from pathlib import Path

ROOT = Path(r"c:\Users\asus\heretic-work")

# 1. Update core Python files
core_dir = ROOT / "core"
for py_file in core_dir.glob("*.py"):
    text = py_file.read_text(encoding="utf-8")
    if "SO NAIVE" in text:
        new_text = text.replace("SO NAIVE IDE", "PRUBETH IDE").replace("SO NAIVE", "PRUBETH")
        py_file.write_text(new_text, encoding="utf-8")
        print(f"Patched: {py_file.relative_to(ROOT)}")

# 2. Update local_ai_studio_pro.py
studio_path = ROOT / "local_ai_studio_pro.py"
if studio_path.exists():
    text = studio_path.read_text(encoding="utf-8")
    replacements = [
        ("SO NAIVE Core", "PRUBETH AI Core"),
        ("SO NAIVE Vision", "PRUBETH Vision"),
        ("SO NAIVE AI Engine", "PRUBETH AI Engine"),
        ("matching SO NAIVE / PRUBETH Horizon design", "matching PRUBETH Horizon design"),
        ("Flagship Local AI Studio Pro window", "Flagship PRUBETH AI Studio Pro window"),
    ]
    for s, d in replacements:
        text = text.replace(s, d)
    # Also update header comment
    text = re.sub(r"Local AI Studio Pro [^\n]+ Next-Gen Agentic AI IDE", "PRUBETH AI Studio Pro — Next-Gen Agentic AI IDE", text)
    studio_path.write_text(text, encoding="utf-8")
    print("Patched: local_ai_studio_pro.py")

# 3. Update tests/test_studio.py
test_path = ROOT / "tests" / "test_studio.py"
if test_path.exists():
    text = test_path.read_text(encoding="utf-8")
    text = text.replace('"publisher": "SO NAIVE"', '"publisher": "PRUBETH"')
    test_path.write_text(text, encoding="utf-8")
    print("Patched: tests/test_studio.py")

# 4. Update CONTRIBUTING.md
contrib_path = ROOT / "CONTRIBUTING.md"
if contrib_path.exists():
    text = contrib_path.read_text(encoding="utf-8")
    text = text.replace("SO NAIVE IDE", "PRUBETH IDE").replace("SO NAIVE", "PRUBETH")
    contrib_path.write_text(text, encoding="utf-8")
    print("Patched: CONTRIBUTING.md")

# 5. Update website files in developments_stack/website/website/
website_dir = ROOT / "developments_stack" / "website" / "website"
if website_dir.exists():
    for f in website_dir.rglob("*"):
        if f.is_file() and f.suffix in [".html", ".md", ".js"]:
            try:
                t = f.read_text(encoding="utf-8", errors="ignore")
                if "SO NAIVE" in t:
                    nt = t.replace("SO NAIVE IDE", "PRUBETH IDE").replace("SO NAIVE", "PRUBETH")
                    f.write_text(nt, encoding="utf-8")
                    print(f"Patched: {f.relative_to(ROOT)}")
            except Exception as e:
                print(f"Error patching {f}: {e}")

print("Universal PRUBETH Branding Application Complete!")
