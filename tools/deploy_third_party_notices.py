import shutil
from pathlib import Path

src = Path(r"c:\Users\asus\heretic-work\ThirdPartyNotices.txt")
targets = [
    Path(r"E:\PRUBETH IDE\ThirdPartyNotices.txt"),
    Path(r"c:\Users\asus\heretic-work\VSCode-win32-x64\ThirdPartyNotices.txt"),
    Path(r"E:\PRUBETH IDE\resources\app\ThirdPartyNotices.txt"),
    Path(r"c:\Users\asus\heretic-work\VSCode-win32-x64\resources\app\ThirdPartyNotices.txt"),
]

for target in targets:
    if target.parent.exists():
        shutil.copy2(src, target)
        print(f"Copied ThirdPartyNotices.txt -> {target}")

print("ThirdPartyNotices deployment complete!")
