# PRUBETH IDE - Strix Security Assessment Runner
param(
    [string]$Target = "c:\Users\asus\heretic-work",
    [string]$Model = "",
    [string]$ApiKey = "",
    [switch]$Headless
)

$ErrorActionPreference = "Continue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "         PRUBETH IDE - STRIX SECURITY AUDIT RUNNER          " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Reload full environment PATH from registry to ensure all newly added tools are active
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$env:PATH = "$userPath;$machinePath"

$strixDir = "C:\Users\asus\.strix\bin"
$dockerDir = "C:\Users\asus\AppData\Local\Programs\DockerDesktop\resources\bin"

if ($env:PATH -notlike "*$strixDir*") {
    $env:PATH = "$strixDir;$env:PATH"
}
if ($env:PATH -notlike "*$dockerDir*") {
    $env:PATH = "$dockerDir;$env:PATH"
}

# 2. Verify strix.exe exists
if (-not (Test-Path "$strixDir\strix.exe")) {
    Write-Host "[ERROR] strix.exe not found in $strixDir" -ForegroundColor Red
    exit 1
}

# 3. Check Docker Desktop daemon
Write-Host "[INFO] Checking Docker daemon status..." -ForegroundColor Yellow
$dockerWorking = $false
try {
    $null = & "$dockerDir\docker.exe" info 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerWorking = $true
        Write-Host "[OK] Docker Engine is running." -ForegroundColor Green
    }
} catch {
    $dockerWorking = $false
}

if (-not $dockerWorking) {
    Write-Host "[WARN] Docker engine is not currently active." -ForegroundColor Yellow
    Write-Host "[INFO] Launching Docker Desktop in the background..." -ForegroundColor Cyan
    $dockerExe = "C:\Users\asus\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe"
    if (Test-Path $dockerExe) {
        Start-Process $dockerExe
        Write-Host "[INFO] Docker Desktop launched. Please ensure the whale icon is running." -ForegroundColor Yellow
    }
}

# 4. Resolve API Key & Model
$selectedKey = $ApiKey
$selectedModel = $Model

if (-not $selectedKey) {
    if ($env:GEMINI_API_KEY) {
        $selectedKey = $env:GEMINI_API_KEY
        if (-not $selectedModel) { $selectedModel = "gemini/gemini-3.8-flash" }
        Write-Host "[INFO] Using GEMINI_API_KEY ($selectedModel)" -ForegroundColor Green
    } elseif ($env:OPENROUTER_API_KEY) {
        $selectedKey = $env:OPENROUTER_API_KEY
        if (-not $selectedModel) { $selectedModel = "openrouter/deepseek/deepseek-r1" }
        Write-Host "[INFO] Using OPENROUTER_API_KEY ($selectedModel)" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[WARN] No API Key found in environment variables." -ForegroundColor Yellow
        $keyInput = Read-Host "Enter your Gemini or OpenRouter API Key"
        if ($keyInput) {
            $selectedKey = $keyInput.Trim()
            if ($selectedKey -like "AIzaSy*") {
                if (-not $selectedModel) { $selectedModel = "gemini/gemini-3.8-flash" }
            } else {
                if (-not $selectedModel) { $selectedModel = "openrouter/deepseek/deepseek-r1" }
            }
        } else {
            Write-Host "[ERROR] An API Key is required to run the AI security assessment." -ForegroundColor Red
            exit 1
        }
    }
}

$env:STRIX_LLM = $selectedModel
$env:LLM_API_KEY = $selectedKey

Write-Host ""
Write-Host "[INFO] Target: $Target" -ForegroundColor Cyan
Write-Host "[INFO] Model:  $selectedModel" -ForegroundColor Cyan
Write-Host "[INFO] Launching Strix Security Assessment..." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

if ($Headless) {
    & "$strixDir\strix.exe" --target $Target -n
} else {
    & "$strixDir\strix.exe" --target $Target
}
