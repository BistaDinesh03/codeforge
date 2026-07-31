<#
.SYNOPSIS
    CodeForge Server Windows Installer v1.0
.DESCRIPTION
    Professional installer with pre-flight checks, progress bars, and uninstall support.
    Run: powershell -ExecutionPolicy Bypass -File install-windows.ps1
#>

param(
    [string]$InstallPath = "C:\CodeForge",
    [switch]$NoModel,
    [switch]$Repair,
    [switch]$Uninstall,
    [switch]$Silent
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerSource = Join-Path (Join-Path $ScriptDir "..") "server"
$AppName = "CodeForge Server"
$MinDiskGB = 5
$MinRAMGB = 4
$MinPython = "3.11"

# ─── Colors ───
function Write-Step { Write-Host "`n>> $args" -ForegroundColor Cyan }
function Write-OK { Write-Host "   OK: $args" -ForegroundColor Green }
function Write-Warn { Write-Host "   WARN: $args" -ForegroundColor Yellow }
function Write-Fail { Write-Host "   FAIL: $args" -ForegroundColor Red; exit 1 }

# ─── Progress Bar ───
function Show-Progress {
    param([int]$Percent, [string]$Status)
    $width = 40
    $filled = [math]::Floor($Percent * $width / 100)
    $empty = $width - $filled
    $bar = "[" + ("#" * $filled) + ("-" * $empty) + "]"
    Write-Host "`r$bar $Percent% $Status" -NoNewline -ForegroundColor Cyan
    if ($Percent -eq 100) { Write-Host "" }
}

# ─── Uninstall Mode ───
if ($Uninstall) {
    Write-Host "Uninstalling $AppName..." -ForegroundColor Yellow
    if (Test-Path $InstallPath) {
        Remove-Item $InstallPath -Recurse -Force
        Write-OK "Removed $InstallPath"
    }
    $desktop = Join-Path ([Environment]::GetFolderPath("Desktop")) "$AppName.lnk"
    if (Test-Path $desktop) { Remove-Item $desktop -Force; Write-OK "Removed desktop shortcut" }
    Write-Host "Uninstall complete." -ForegroundColor Green
    Read-Host "Press Enter to exit"
    exit 0
}

# ─── Banner ───
Clear-Host
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   $AppName Installer v1.0" -ForegroundColor Cyan
Write-Host "   Private AI Coding Assistant" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Install location: $InstallPath" -ForegroundColor White
Write-Host ""

# ─── Pre-flight Checks ───
Write-Step "Pre-flight checks..."

# Check disk space
$drive = $InstallPath.Substring(0, 1) + ":"
$disk = Get-PSDrive -Name $drive.Substring(0, 1)
$freeGB = [math]::Round($disk.Free / 1GB, 1)
if ($freeGB -lt $MinDiskGB) {
    Write-Fail "Only ${freeGB}GB free. Need at least ${MinDiskGB}GB."
}
Write-OK "Disk space: ${freeGB}GB free (need ${MinDiskGB}GB)"

# Check RAM
$ram = Get-CimInstance Win32_ComputerSystem
$ramGB = [math]::Round($ram.TotalPhysicalMemory / 1GB)
if ($ramGB -lt $MinRAMGB) {
    Write-Warn "Only ${ramGB}GB RAM. Server may be slow. ${MinRAMGB}GB+ recommended."
} else {
    Write-OK "RAM: ${ramGB}GB (need ${MinRAMGB}GB)"
}

# Check Python
$pythonCmd = $null
try {
    $pyVersion = python --version 2>&1
    $pyMajor = [int]($pyVersion -replace "Python ","").Split(".")[0]
    $pyMinor = [int]($pyVersion -replace "Python ","").Split(".")[1]
    if ($pyMajor -lt 3 -or ($pyMajor -eq 3 -and $pyMinor -lt 11)) {
        Write-Fail "Python $pyVersion found. Need Python ${MinPython}+. Install from https://www.python.org/downloads/"
    }
    Write-OK "Python: $pyVersion"
    $pythonCmd = "python"
} catch {
    Write-Fail "Python not found. Install Python ${MinPython}+ from https://www.python.org/downloads/"
}

# ─── Repair Mode ───
if ($Repair) {
    Write-Step "Repairing installation..."
    if (-not (Test-Path $InstallPath)) {
        Write-Fail "No installation found at $InstallPath. Run without --Repair to install."
    }
    Write-OK "Installation found, reinstalling dependencies..."
}

# ─── Step 1: Create directories ───
Show-Progress 5 "Creating directories"
New-Item -Path $InstallPath -ItemType Directory -Force | Out-Null
New-Item -Path "$InstallPath\models" -ItemType Directory -Force | Out-Null
New-Item -Path "$InstallPath\logs" -ItemType Directory -Force | Out-Null
Show-Progress 10 "Directories ready"

# ─── Step 2: Copy server files ───
Show-Progress 15 "Copying server files"
if (Test-Path $ServerSource) {
    Copy-Item -Path "$ServerSource\*" -Destination $InstallPath -Recurse -Force -Exclude "venv","__pycache__","*.pyc","models\*.gguf"
} else {
    Write-Fail "Server source not found at $ServerSource"
}
Show-Progress 30 "Server files copied"

# ─── Step 3: Install Python packages ───
Show-Progress 35 "Creating virtual environment"
Push-Location $InstallPath
try {
    if (Test-Path "venv") { Remove-Item "venv" -Recurse -Force }
    & $pythonCmd -m venv venv
    $activatePath = Join-Path $InstallPath "venv\Scripts\Activate.ps1"
    . $activatePath
    
    Show-Progress 40 "Upgrading pip"
    pip install --quiet --upgrade pip 2>&1 | Out-Null
    
    Show-Progress 50 "Installing FastAPI"
    pip install --quiet fastapi uvicorn pydantic pydantic-settings 2>&1 | Out-Null
    
    Show-Progress 65 "Installing llama.cpp"
    pip install --quiet llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu 2>&1 | Out-Null
    
    deactivate
    Show-Progress 75 "Packages installed"
} finally {
    Pop-Location
}

# ─── Step 4: Download model ───
if (-not $NoModel) {
    $modelName = "Qwen2.5-Coder-1.5B-Instruct-Q4_K_M.gguf"
    $modelPath = Join-Path $InstallPath "models" $modelName
    
    if (Test-Path $modelPath) {
        Show-Progress 90 "Model already installed"
    } else {
        Show-Progress 80 "Downloading AI model (940 MB)"
        $modelUrl = "https://huggingface.co/bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/$modelName"
        Invoke-WebRequest -Uri $modelUrl -OutFile $modelPath
        Show-Progress 90 "Model downloaded"
    }
} else {
    Show-Progress 90 "Model skipped"
}

# ─── Step 5: Create shortcuts ───
Show-Progress 92 "Creating shortcuts"

$startBat = @"
@echo off
title $AppName
cd /d "$InstallPath"
call venv\Scripts\activate
:loop
echo ============================================
echo   $AppName
echo   http://localhost:8000
echo ============================================
echo Starting server... (auto-restarts if crashed)
uvicorn app.main:app --host 0.0.0.0 --port 8000
echo Server stopped. Restarting in 3 seconds...
timeout /t 3 >nul
goto loop
"@
$startBatPath = Join-Path $InstallPath "Start Server.bat"
$startBat | Out-File -FilePath $startBatPath -Encoding ASCII

# Uninstall script
$uninstallBat = @"
@echo off
echo Uninstalling $AppName...
powershell -ExecutionPolicy Bypass -File "$ScriptDir\install-windows.ps1" -Uninstall
"@
$uninstallBatPath = Join-Path $InstallPath "Uninstall.bat"
$uninstallBat | Out-File -FilePath $uninstallBatPath -Encoding ASCII

# Desktop shortcut
try {
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktopPath "$AppName.lnk"
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = $startBatPath
    $Shortcut.WorkingDirectory = $InstallPath
    $Shortcut.Description = "CodeForge - Private AI Coding Server"
    $Shortcut.Save()
} catch { }

Show-Progress 100 "Complete"

# ─── Done ───
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "   Installation Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Desktop: Double-click '$AppName'" -ForegroundColor White
Write-Host "  Dashboard: http://localhost:8000" -ForegroundColor White
Write-Host "  Uninstall: $uninstallBatPath" -ForegroundColor White
Write-Host ""

if (-not $Silent) {
    Read-Host "Press Enter to finish"
}