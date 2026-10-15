import sys
import os
import time
import subprocess
from pathlib import Path

out_dir = Path(r"C:\Users\asus\.gemini\antigravity\brain\b788f130-97a4-4645-aad4-e48e53d731d3")
out_dir.mkdir(parents=True, exist_ok=True)

from PyQt5.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)
screen = app.primaryScreen()

# 1. Terminate old PRUBETH processes
print("[1/5] Terminating old PRUBETH instances...")
subprocess.run(["powershell", "-NoProfile", "-Command", "Stop-Process -Name PRUBETH -Force -ErrorAction SilentlyContinue"], capture_output=True)
time.sleep(1.5)

# 2. Launch PRUBETH.exe
exe = r"E:\PRUBETH IDE\PRUBETH.exe"
print(f"[2/5] Launching {exe}...")
proc = subprocess.Popen(
    [exe, r"c:\Users\asus\heretic-work"],
    creationflags=0x00000008 | 0x00000200, # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    close_fds=True
)
print(f"      PID: {proc.pid}")

# 3. Wait 1.8s to capture loading phase
print("[3/5] Capturing loading holographic screen...")
time.sleep(1.8)
pix_loading = screen.grabWindow(0)
loading_path = out_dir / "prubeth_loading_holograph.png"
pix_loading.save(str(loading_path), "PNG")
print(f"      Saved loading screen: {loading_path} ({pix_loading.width()}x{pix_loading.height()})")

# 4. Wait for workbench to settle
print("[4/5] Waiting for workbench layout to complete...")
time.sleep(4.5)
pix_live = screen.grabWindow(0)
live_path = out_dir / "prubeth_ide_desktop_live.png"
pix_live.save(str(live_path), "PNG")
print(f"      Saved workbench screen: {live_path} ({pix_live.width()}x{pix_live.height()})")

# 5. Check processes
res = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Process -Name PRUBETH -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count"], capture_output=True, text=True)
cnt = res.stdout.strip()
print(f"[5/5] Active PRUBETH processes: {cnt}")
print("SUCCESS: Restart and capture completed perfectly!")
