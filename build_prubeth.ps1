# PRUBETH IDE -- Complete Build & Installer Pipeline (PowerShell)
# Stages: npm install -> gulp compile -> gulp package -> icons -> Inno Setup
# Run from: C:\Users\asus\heretic-work
# Usage: .\build_prubeth.ps1 [-SkipNpm] [-SkipCompile] [-OnlyInno]

param(
    [switch]$SkipNpm,
    [switch]$SkipCompile,
    [switch]$OnlyInno
)

$ErrorActionPreference = "Stop"

# Fix PATH to include all system & user paths
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
$env:VSCODE_SKIP_NODE_VERSION_CHECK = "1"
$env:ELECTRON_SKIP_BINARY_DOWNLOAD = "1"

$ROOT     = "C:\Users\asus\heretic-work"
$VSCODE   = "$ROOT\vscode"
$ASSETS   = "$ROOT\assets"
$DIST     = "$ROOT\dist"
$BUILD    = "$ROOT\prubeth-build"
$ISCC     = "C:\Users\asus\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
$ISS      = "$VSCODE\build\win32\prubeth.iss"
$APP_VER  = "1.89.0"

function Write-Stage($n, $msg) {
    Write-Host ""
    Write-Host "+$('='*($msg.Length+4))+" -ForegroundColor Cyan
    Write-Host "|  STAGE $n -- $msg  |" -ForegroundColor Cyan
    Write-Host "+$('='*($msg.Length+4))+" -ForegroundColor Cyan
    Write-Host ""
}

# ── Stage 2: npm install ─────────────────────────────────────────────────────
if (-not $SkipNpm -and -not $SkipCompile -and -not $OnlyInno) {
    Write-Stage 2 "npm install (VS Code dependencies)"
    Push-Location $VSCODE
    & npm install --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) { Write-Error "npm install failed!" }
    Pop-Location
    Write-Host "  [OK] npm install complete." -ForegroundColor Green
}

# ── Stage 3: Gulp compile (TypeScript -> JavaScript) ─────────────────────────
if (-not $SkipCompile -and -not $OnlyInno) {
    Write-Stage 3 "Gulp compile-client (TypeScript -> JS)"
    Push-Location $VSCODE
    & node node_modules/gulp/bin/gulp.js compile-client
    if ($LASTEXITCODE -ne 0) { Write-Error "Gulp compile-client failed!" }
    Pop-Location
    Write-Host "  [OK] TypeScript compilation complete." -ForegroundColor Green
}

# ── Stage 4: Gulp package win32-x64 ──────────────────────────────────────────
if (-not $SkipCompile -and -not $OnlyInno) {
    Write-Stage 4 "Gulp package vscode-win32-x64"
    Push-Location $VSCODE
    & node node_modules/gulp/bin/gulp.js vscode-win32-x64
    if ($LASTEXITCODE -ne 0) { Write-Error "Gulp vscode-win32-x64 failed!" }
    Pop-Location

    $gulpOut = "$ROOT\..\VSCode-win32-x64"
    if (Test-Path $gulpOut) {
        Write-Host "  [OK] Package output found at: $gulpOut" -ForegroundColor Green
        if (Test-Path $BUILD) { Remove-Item -Recurse -Force $BUILD }
        Copy-Item -Recurse $gulpOut $BUILD
        Write-Host "  [OK] Copied to: $BUILD" -ForegroundColor Green
    } else {
        # Try alternate locations
        $altOut = "$ROOT\VSCode-win32-x64"
        if (Test-Path $altOut) {
            if (Test-Path $BUILD) { Remove-Item -Recurse -Force $BUILD }
            Copy-Item -Recurse $altOut $BUILD
            Write-Host "  [OK] Package output: $BUILD" -ForegroundColor Green
        } else {
            Write-Warning "  [WARN] Could not find VSCode-win32-x64 output. Check gulp task."
        }
    }
    Write-Host "  [OK] Packaging complete." -ForegroundColor Green
}

# ── Stage 5: Deploy PRUBETH Icons into Final Build ───────────────────────────
if (-not $OnlyInno) {
    Write-Stage 5 "Deploying PRUBETH branding into final build"
    if (Test-Path $BUILD) {
        # Replace all .ico files with PRUBETH icon
        Get-ChildItem -Recurse -Path $BUILD -Filter "*.ico" | ForEach-Object {
            Copy-Item -Force "$ASSETS\icon.ico" $_.FullName
            Write-Host "  [OK] Replaced: $($_.Name)" -ForegroundColor Green
        }
        # Replace product.json in built app
        $finalProduct = "$BUILD\resources\app\product.json"
        if (Test-Path $finalProduct) {
            Copy-Item -Force "$VSCODE\product.json" $finalProduct
            Write-Host "  [OK] Deployed PRUBETH product.json to build." -ForegroundColor Green
        }
        # Deploy assets folder
        $assetsDest = "$BUILD\assets"
        if (-not (Test-Path $assetsDest)) { New-Item -Type Directory $assetsDest | Out-Null }
        Copy-Item -Force "$ASSETS\*" $assetsDest
        Write-Host "  [OK] Brand assets deployed to $assetsDest" -ForegroundColor Green
    } else {
        Write-Warning "  [WARN] prubeth-build not found. Skipping icon deployment."
    }
}

# ── Stage 6: Generate Wizard BMPs ────────────────────────────────────────────
Write-Stage 6 "Building Installer (Inno Setup 6)"
Write-Host "  Generating wizard BMP images..." -ForegroundColor Yellow

$wizardBig   = "$VSCODE\build\win32\prubeth-wizard-big.bmp"
$wizardSmall = "$VSCODE\build\win32\prubeth-wizard-small.bmp"

if (-not (Test-Path $wizardBig)) {
    # Copy VS Code's own BMP as base (will be overridden by Pillow if available)
    Copy-Item "$VSCODE\build\win32\inno-big-100.bmp" $wizardBig -Force
    Copy-Item "$VSCODE\build\win32\inno-small-100.bmp" $wizardSmall -Force
    Write-Host "  [OK] Wizard BMPs prepared (using VS Code base, PRUBETH logo on pages)" -ForegroundColor Green
}

# Try Python/Pillow BMP generation
$bmpy = @"
import sys
try:
    from PIL import Image
    img = Image.open(r'$ASSETS\logo.png').convert('RGB')
    big = img.resize((164, 314), Image.LANCZOS)
    big.save(r'$wizardBig', 'BMP')
    small = img.resize((55, 55), Image.LANCZOS)
    small.save(r'$wizardSmall', 'BMP')
    print('[OK] Wizard BMPs generated from PRUBETH logo.')
except ImportError:
    print('[WARN] Pillow not available; using VS Code wizard images.')
"@
python -c $bmpy 2>&1

# ── Stage 6b: Run ISCC ───────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Running Inno Setup compiler..." -ForegroundColor Yellow
if (-not (Test-Path $ISS)) {
    Write-Error "  ISS script not found: $ISS"
}

New-Item -ItemType Directory -Force $DIST | Out-Null
& $ISCC $ISS
if ($LASTEXITCODE -ne 0) { Write-Error "Inno Setup compilation failed!" }
Write-Host "  [OK] Inno Setup installer built!" -ForegroundColor Green

# ── Stage 7: Summary ─────────────────────────────────────────────────────────
Write-Stage 7 "Release Summary"
$candidates = Get-ChildItem -Path $DIST -Filter "Prubeth*.exe" | Sort-Object LastWriteTime -Descending
if ($candidates) {
    $exe = $candidates[0]
    $sizeMB = [math]::Round($exe.Length / 1MB, 1)
    Write-Host "  [OK] Installer: $($exe.Name)" -ForegroundColor Green
    Write-Host "  [OK] Size:      $sizeMB MiB" -ForegroundColor Green
    Write-Host "  [OK] Path:      $($exe.FullName)" -ForegroundColor Green
} else {
    Write-Warning "  No installer found in $DIST"
}

Write-Host ""
Write-Host "  Built:     $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "  Publisher: BSVR Technologies" -ForegroundColor Cyan
Write-Host "  Website:   https://www.bsvr.work/" -ForegroundColor Cyan
Write-Host ""
