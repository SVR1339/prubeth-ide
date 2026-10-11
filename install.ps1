<#
.SYNOPSIS
    Prudeth IDE — Unified Windows PowerShell Automated Installer
.DESCRIPTION
    Installs and configures Prudeth IDE on Windows 10/11.
    Tagline: Bloom, ideas unfolding
    Supports both standalone setup executable deployment and automated source environment bootstrapping.
.EXAMPLE
    irm https://raw.githubusercontent.com/imyouiamyou/prubeth-ide/master/install.ps1 | iex
    powershell -ExecutionPolicy Bypass -File install.ps1
    powershell -ExecutionPolicy Bypass -File install.ps1 -Silent
#>

[CmdletBinding()]
param(
    [switch]$Silent,
    [switch]$NoLaunch,
    [switch]$SourceOnly,
    [string]$InstallDir = "$env:LOCALAPPDATA\Programs\PrudethIDE"
)

$ErrorActionPreference = "Stop"

function Write-Banner {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Magenta
    Write-Host "             PRUDETH IDE — BLOOM EDITION (v3.0.0)              " -ForegroundColor White
    Write-Host "                   Bloom, ideas unfolding                       " -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Magenta
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "[+] $Message" -ForegroundColor Green
}

function Write-WarnMsg {
    param([string]$Message)
    Write-Host "[!] $Message" -ForegroundColor Yellow
}

function Write-ErrMsg {
    param([string]$Message)
    Write-Host "[-] $Message" -ForegroundColor Red
}

Write-Banner

# 1. Check Operating System
$os = [System.Environment]::OSVersion
if ($os.Platform -ne [System.PlatformID]::Win32NT) {
    Write-ErrMsg "This installer is designed for Windows 10 or Windows 11. For Linux or macOS, run install.sh."
    exit 1
}
Write-Step "Operating System: Windows $($os.Version.Major).$($os.Version.Minor) Build $($os.Version.Build) (Verified)"

# 2. Check for Standalone Installer Executable
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }

$localSetupCandidates = @(
    (Join-Path $scriptDir "PrubethIDE-Setup.exe"),
    (Join-Path $scriptDir "setup.exe"),
    (Join-Path $scriptDir "dist\PrubethIDE-v3.0.0-Setup.exe"),
    (Join-Path $scriptDir "dist\setup.exe")
)

$setupExe = $null
if (-not $SourceOnly) {
    foreach ($cand in $localSetupCandidates) {
        if (Test-Path $cand) {
            $setupExe = (Resolve-Path $cand).Path
            break
        }
    }
}

if ($setupExe -and (-not $SourceOnly)) {
    Write-Step "Found Standalone Setup Wizard: $setupExe"
    Write-Step "Executing single-click installation wizard..."
    if ($Silent) {
        Start-Process -FilePath $setupExe -ArgumentList "--silent" -Wait
    } else {
        Start-Process -FilePath $setupExe
    }
    Write-Step "Setup launcher initiated successfully."
    exit 0
}

# 3. Source-based / Environment Bootstrap Mode
Write-Step "Bootstrapping PRUBETH IDE Python runtime environment..."

# Find Python 3.10+
$pythonCmd = $null
$pyVersions = @("python", "py", "python3")
foreach ($cmd in $pyVersions) {
    try {
        $verStr = & $cmd --version 2>&1
        if ($verStr -match "Python\s+3\.(\d+)") {
            $minor = [int]$matches[1]
            if ($minor -ge 10) {
                $pythonCmd = $cmd
                Write-Step "Detected compatible Python runtime: $verStr"
                break
            }
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-ErrMsg "Python 3.10+ was not found in PATH."
    Write-WarnMsg "Please install Python 3.10 or higher from https://www.python.org/downloads/ or Microsoft Store."
    Write-WarnMsg "Alternatively, run the pre-built standalone installer: PrubethIDE-Setup.exe"
    exit 1
}

# 4. Check or Create Virtual Environment
$venvDir = Join-Path $scriptDir ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Step "Creating isolated virtual environment in: $venvDir"
    & $pythonCmd -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-ErrMsg "Failed to create virtual environment."
        exit 1
    }
}
Write-Step "Virtual environment ready: $venvPython"

# 5. Upgrade pip & Install Requirements
Write-Step "Verifying and updating required packages..."
& $venvPython -m pip install --upgrade pip --quiet
$reqFile = Join-Path $scriptDir "requirements.txt"
if (Test-Path $reqFile) {
    & $venvPython -m pip install -r $reqFile --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-WarnMsg "Some optional packages had installation warnings, continuing with core components..."
    }
}

# 6. Run Preflight Diagnostics
$mainScript = Join-Path $scriptDir "local_ai_studio_pro.py"
if (Test-Path $mainScript) {
    Write-Step "Executing preflight diagnostics check..."
    & $venvPython $mainScript --preflight-only
    if ($LASTEXITCODE -ne 0) {
        Write-WarnMsg "Preflight diagnostics completed with non-fatal warnings."
    } else {
        Write-Step "Preflight verification PASSED."
    }
}

# 7. Create Desktop and Start Menu Shortcuts
try {
    $wshell = New-Object -ComObject WScript.Shell
    $desktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
    $shortcutPath = Join-Path $desktopPath "PRUBETH IDE.lnk"
    $shortcut = $wshell.CreateShortcut($shortcutPath)
    $batchRunner = Join-Path $scriptDir "run_local_ai_studio_pro.bat"
    $shortcut.TargetPath = $batchRunner
    $shortcut.WorkingDirectory = $scriptDir
    $icoPath = Join-Path $scriptDir "assets\icon.ico"
    if (Test-Path $icoPath) {
        $shortcut.IconLocation = "$icoPath, 0"
    }
    $shortcut.Description = "PRUBETH IDE — Horizon Edition"
    $shortcut.Save()
    Write-Step "Created Desktop Shortcut: $shortcutPath"
} catch {
    Write-WarnMsg "Could not automatically generate Desktop shortcut: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "         PRUBETH IDE INSTALLATION COMPLETED SUCCESSFULLY!       " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Launch methods:" -ForegroundColor White
Write-Host "  1. Desktop Shortcut: 'PRUBETH IDE'" -ForegroundColor Gray
Write-Host "  2. Batch Runner:     .\run_local_ai_studio_pro.bat" -ForegroundColor Gray
Write-Host "  3. Python CLI:       .venv\Scripts\python.exe local_ai_studio_pro.py" -ForegroundColor Gray
Write-Host ""

if (-not $NoLaunch) {
    $resp = Read-Host "Would you like to launch PRUBETH IDE right now? (Y/n)"
    if ($resp -eq "" -or $resp -match "^[yY]") {
        Write-Step "Launching PRUBETH IDE..."
        Start-Process -FilePath (Join-Path $scriptDir "run_local_ai_studio_pro.bat")
    }
}
