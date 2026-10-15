from pathlib import Path

SOVEREIGN_LICENSE = """PRUBETH IDE
Copyright (c) 2026 BSVR Technologies. All rights reserved.
Official Watermark: "DONT HIRE ROBOTS - JUST USE IT"

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

------------------------------------------------------------------------
Portions of this software are derived from open-source Code - OSS:
Copyright (c) 2015 - present Microsoft Corporation
Full third-party notices and open-source licenses are provided in ThirdPartyNotices.txt.
"""

targets = [
    Path(r"c:\Users\asus\heretic-work\LICENSE"),
    Path(r"c:\Users\asus\heretic-work\LICENSE.txt"),
    Path(r"E:\PRUBETH IDE\LICENSE.txt"),
    Path(r"E:\PRUBETH IDE\resources\app\LICENSE.txt"),
    Path(r"c:\Users\asus\heretic-work\VSCode-win32-x64\LICENSE.txt"),
    Path(r"c:\Users\asus\heretic-work\VSCode-win32-x64\resources\app\LICENSE.txt"),
]

for t in targets:
    if t.parent.exists():
        t.write_text(SOVEREIGN_LICENSE, encoding="utf-8")
        print(f"Updated sovereign LICENSE -> {t}")

print("Sovereign license deployment complete!")
