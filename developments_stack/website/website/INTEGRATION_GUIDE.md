# Deployment & Integration Guide: https://www.bsvr.work/

This guide documents the full proceedings, website updates, removal of the flying doll widget, and deployment instructions for **PRUBETH IDE (v3.0.0 Horizon Edition)** on **[https://www.bsvr.work/](https://www.bsvr.work/)**.

---

## 🚀 1. What Has Been Updated

### A. Flying Doll / Cupid Feature Completely Removed
- **Identified Component:** The peeping Cupid / "God of Love" widget (`#god-of-love`, `.god-of-love-container`, `.cupid-body`, `.cupid-3d-img`, `.love-particle`) and its associated animations (`floatLove`, `loveRise`, `peepOut`, `spawnLoveParticles`, `triggerLoveBurst`).
- **Resolution:** 100% excised from HTML, CSS styles, and JavaScript runtime. The page is now clean, sleek, and distraction-free.

### B. Flagship PRUBETH IDE Showcase Section Added
- **Dedicated Section (`#projects`):** Seamlessly positioned in the core portfolio layout with glassmorphic styling matching Apple Vision Pro aesthetics.
- **Cybernetic Blinking Beacon:** Real-time pulsing cyan indicator signaling live IDE status.
- **Dynamic Client-Side OS Detection:** Automatically detects whether the visitor is on Windows, macOS, or Linux, and renders the tailored primary download CTA pill button:
  - Windows visitors see: **`Download for Windows ⤓`** (links directly to `SoNaive-v3.0.0-Setup.exe` / `setup.exe`)
  - macOS visitors see: **`Download for macOS ⤓`** (links to `SoNaive-v3.0.0-macOS.dmg`)
  - Linux visitors see: **`Download for Linux ⤓`** (links to `SoNaive-v3.0.0-Linux.deb`)
- **Expandable Mirrors & Formats Menu:** 1-click dropdown for Setup Executable, Universal setup.exe, Portable ZIP, macOS DMG, Debian package, and Linux Tarball.
- **Live IDE Terminal Mockup:** Displaying active GPU acceleration gauge (`[GTX 1050 Ti · CUDA 12.6]`), Intelligent Model Cascade, 1-click Auto-Fix diff engine, and deliverable verification.
- **Core Specifications Matrix:** 128KB Complete File Context, 4-tier router cascade, 1-click AI Auto-Fix compiler, autonomous agent loop, and Dual MIT / Apache 2.0 permissive license.

### C. Top & Mobile Navigation Updated
- Direct **`Projects (PRUBETH)`** link added with blinking cybernetic beacon to:
  - Fixed desktop glass navbar (`<header class="navbar">`)
  - Mobile slide-out drawer menu (`<div class="mobile-menu-drawer">`)

---

## 📁 2. Ready-to-Deploy Files in `website/`

| File | Purpose |
| :--- | :--- |
| **[`website/index.html`](file:///c:/Users/asus/heretic-work/website/index.html)** | **Complete, standalone drop-in replacement for the entire homepage.** Flying doll removed + PRUBETH IDE project section integrated. (102.5 KB) |
| **[`website/so_naive_project_section.html`](file:///c:/Users/asus/heretic-work/website/so_naive_project_section.html)** | Standalone HTML section block for embedding into existing pages or IFrames. |
| **[`website/SoNaiveProjectSection.jsx`](file:///c:/Users/asus/heretic-work/website/SoNaiveProjectSection.jsx)** | React / Next.js / Tailwind CSS component for modern frontend frameworks. |

---

## 🌐 3. How to Deploy to https://www.bsvr.work/

### Method 1: Direct File Replacement (Easiest & Fastest)
If your site is hosted via static hosting (GitHub Pages, Cloudflare Pages, Vercel, or cPanel/FTP):
1. Copy the updated file [`website/index.html`](file:///c:/Users/asus/heretic-work/website/index.html).
2. Replace the root `index.html` file in your website hosting repository or web root folder.
3. Commit & push (or upload). The site will immediately reflect the new project section and the removal of the flying doll.

### Method 2: For React / Next.js Frameworks
If your portfolio uses React or Next.js:
1. Copy `website/SoNaiveProjectSection.jsx` to your components directory (e.g. `components/projects/SoNaiveProjectSection.jsx`).
2. Import and place `<SoNaiveProjectSection />` inside your page.

---

## 📦 4. Release Download URLs

All buttons on the website link directly to verified GitHub release assets:

| Platform | Download Asset | Direct Release Link |
| :--- | :--- | :--- |
| **Windows Setup (Recommended)** | `SoNaive-v3.0.0-Setup.exe` (36.5 MB) | `https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-Setup.exe` |
| **Windows Quick Setup** | `setup.exe` (36.5 MB) | `https://github.com/bsvr/so-naive/releases/latest/download/setup.exe` |
| **Windows Portable** | `SoNaive-v3.0.0-Windows-Portable.zip` | `https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-Windows-Portable.zip` |
| **Apple macOS** | `SoNaive-v3.0.0-macOS.dmg` | `https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-macOS.dmg` |
| **Ubuntu / Debian** | `SoNaive-v3.0.0-Linux.deb` | `https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-Linux.deb` |
| **Linux Universal** | `SoNaive-v3.0.0-Linux-x86_64.tar.gz` | `https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-Linux-x86_64.tar.gz` |
