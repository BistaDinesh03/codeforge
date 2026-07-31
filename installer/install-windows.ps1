<#
.SYNOPSIS
    CodeForge Server Windows Installer
.DESCRIPTION
    One-click installer for CodeForge. Double-click the script or run:
    powershell -ExecutionPolicy Bypass -File install-windows.ps1
#>

param(
    [string]$InstallPath = "C:\CodeForge",
    [switch]$NoModel,
    [switch]$StartAfterInstall,
    [switch]$Silent
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerSource = Join-Path (Join-Path $ScriptDir "..") "server"
Clear-Host
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   CodeForge Server Installer v1.0" -ForegroundColor Cyan
Write-Host "   Private AI Coding Assistant" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Install location: $InstallPath" -ForegroundColor White
Write-Host ""

Write-Host "[1/6] Creating directories..." -ForegroundColor Yellow
New-Item -Path $InstallPath -ItemType Directory -Force | Out-Null
New-Item -Path "$InstallPath\models" -ItemType Directory -Force | Out-Null
New-Item -Path "$InstallPath\logs" -ItemType Directory -Force | Out-Null
Write-Host "  OK: Install directory ready" -ForegroundColor Green

Write-Host "[2/6] Checking Python..." -ForegroundColor Yellow
$pythonCmd = $null
try {
    $v = python --version 2>&1
    Write-Host "  OK: Found $v" -ForegroundColor Green
    $pythonCmd = "python"
} catch {
    Write-Host "  ERROR: Python not found. Install from https://www.python.org/downloads/" -ForegroundColor Red
    if (-not $Silent) { Read-Host "Press Enter to exit" }
    exit 1
}

Write-Host "[3/6] Installing server files..." -ForegroundColor Yellow
if (Test-Path $ServerSource) {
    Copy-Item -Path "$ServerSource\*" -Destination $InstallPath -Recurse -Force -Exclude "venv","__pycache__","*.pyc","models\*.gguf"
    Write-Host "  OK: Server files copied" -ForegroundColor Green
} else {
    Write-Host "  Server source not found at $ServerSource" -ForegroundColor Red
    exit 1
}

Write-Host "[4/6] Installing Python packages..." -ForegroundColor Yellow
Push-Location $InstallPath
try {
    & $pythonCmd -m venv venv
    $activatePath = Join-Path $InstallPath "venv\Scripts\Activate.ps1"
    . $activatePath
    pip install --quiet --upgrade pip
    pip install --quiet fastapi uvicorn pydantic pydantic-settings
    pip install --quiet llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
    deactivate
    Write-Host "  OK: Packages installed" -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host "[5/6] Model download..." -ForegroundColor Yellow
if (-not $NoModel) {
    $modelName = "Qwen2.5-Coder-1.5B-Instruct-Q4_K_M.gguf"
    $modelPath = Join-Path $InstallPath "models" $modelName
    if (Test-Path $modelPath) {
        $size = [math]::Round((Get-Item $modelPath).Length / 1MB)
        Write-Host "  OK: Model already exists ($size MB)" -ForegroundColor Green
    } else {
        Write-Host "  Downloading model (940 MB, one-time)..." -ForegroundColor Gray
        $modelUrl = "https://huggingface.co/bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/$modelName"
        Invoke-WebRequest -Uri $modelUrl -OutFile $modelPath
        $size = [math]::Round((Get-Item $modelPath).Length / 1MB)
        Write-Host "  OK: Model downloaded ($size MB)" -ForegroundColor Green
    }
} else {
    Write-Host "  Skipped (use --NoModel)" -ForegroundColor Gray
}

Write-Host "[6/6] Creating shortcuts..." -ForegroundColor Yellow
$startBat = @"
@echo off
title CodeForge Server
cd /d "$InstallPath"
call venv\Scripts\activate
echo CodeForge Server: http://localhost:8000
start http://localhost:8000
uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
"@
$startBatPath = Join-Path $InstallPath "Start Server.bat"
$startBat | Out-File -FilePath $startBatPath -Encoding ASCII

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "CodeForge Server.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $startBatPath
$Shortcut.WorkingDirectory = $InstallPath
$Shortcut.Save()
Write-Host "  OK: Desktop shortcut created" -ForegroundColor Green

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "   Installation Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Desktop: Double-click 'CodeForge Server'" -ForegroundColor White
Write-Host "  Manual:  $startBatPath" -ForegroundColor White
Write-Host ""

if ($StartAfterInstall) {
    Start-Process -FilePath $startBatPath
    Start-Sleep 2
    Start-Process "http://localhost:8000"
}

if (-not $Silent) {
    Read-Host "Press Enter to finish"
}