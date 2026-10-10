# Changelog: SO NAIVE IDE

All notable changes to **SO NAIVE IDE** will be documented in this file.  
Official Website & Downloads: [**https://www.bsvr.work/#projects**](https://www.bsvr.work/#projects)

---

## [3.0.0] - Horizon Edition - 2026-10-09

### Added
- **Official Branding & Persona:** Rebranded as **SO NAIVE IDE** / **NAIVE** — "So Naive, It Solves Everything."
- **Animated Blinking Cybernetic AI Beacon (`BlinkingAIIndicator`):**
  - Smooth 25 FPS sine-wave breathing indicator in the main toolbar and statusbar.
  - Reactive visual states: Idle breathing (cyan), Streaming/Inference chromatic blink (violet/cyan), Auto-Fix strobe (emerald/amber), and Error alert (ruby red).
- **GPU Hardware Status Gauge:** Direct display of active NVIDIA CUDA acceleration (`[GTX 1050 Ti · CUDA 12.6]`) in the permanent statusbar.
- **Universal Cross-Platform Release Matrix (`.github/workflows/release.yml`):**
  - Windows: Automated `SoNaive-v3.0.0-Setup.exe` (Inno Setup 6 + standalone wizard) & `.zip` portable.
  - Apple macOS: Automated `SoNaive-v3.0.0-macOS.dmg` & `.zip` universal bundle.
  - Ubuntu / Debian: Automated `SoNaive-v3.0.0-Linux.deb` & `SoNaive-v3.0.0-Linux-x86_64.tar.gz`.
- **BSVR Project Showcase Web Integration:**
  - Standalone interactive HTML showcase (`website/so_naive_project_section.html`) with dynamic client-side visitor OS detection matching the pill design ("Download for Windows ⤓").
  - Drop-in React/Next.js/Tailwind component (`website/SoNaiveProjectSection.jsx`) for `https://www.bsvr.work/`.
  - Integration guide for webmasters (`website/INTEGRATION_GUIDE.md`).
- **Commercial Licensing & Edition Tiers:** Free Community Edition, Pro Developer ($19/mo or $190 lifetime), and Enterprise Suite ($199/seat) with direct website links to `https://www.bsvr.work/`.
- **Integrated Help & Update Menu:** Actions for "Visit Official Website (bsvr.work)", "Explore Projects on bsvr.work", "Check for Updates", and "Commercial Licensing".
- **Brand Assets:** High-resolution vector `assets/logo.svg`, 512x512 `assets/logo.png`, and multi-resolution Windows icon `assets/icon.ico` (256, 128, 64, 48, 32, 16).

### Improved
- Expanded test suite to 10/10 comprehensive pytest unit and integration tests passing in < 1.0s.
- Enhanced Intelligent Model Router with zero-downtime failover from Google Gemini 3.8 Flash to local GPU Ollama.
- Upgraded traceback auto-fix engine with colorized visual diff review.

---

## [2.4.0] - Antigravity Edition
- Introduced Intelligent Model Router with priority cascade across Gemini 3.8 Flash, Gemini 3.5 Flash, and Ollama.
- Added 1-click `⚡ Auto-Fix with AI` error traceback repair bar.
- Added QScintilla polyglot syntax lexers for Python, JS/TS, C++, Rust, HTML, CSS, JSON, YAML, SQL, and Shell.

---

## [2.0.0] - Foundation Release
- Initial PyQt5 workspace with file tree, multi-tab editor, and basic Ollama local integration.
