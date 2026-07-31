<#
.SYNOPSIS
    CodeForge Server Installer for Windows
.DESCRIPTION
    One-command installer. Downloads everything needed and sets up the server.
    Run: powershell -ExecutionPolicy Bypass -File install-windows.ps1
#>

param(
    [string]$InstallPath = "C:\CodeForge",
    [string]$Model = "qwen-1.5b",  # qwen-1.5b, deepseek-1.3b, or custom
    [switch]$NoModel,
    [switch]$StartOnBoot
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "CodeForge Server Installer"

# ─── Banner ───
Clear-Host
Write-Host @"
============================================
   CodeForge Server Installer
   Private AI Coding Assistant
============================================

This will install:
  • CodeForge Server
  • Python (if needed)
  • AI Model (if selected)

Install location: $InstallPath

"@ -ForegroundColor Cyan

# ─── Step 1: Check Python ───
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow

$pythonCmd = $null
try {
    $version = python --version 2>&1
    Write-Host "  Found: $version" -ForegroundColor Green
    $pythonCmd = "python"
} catch {
    try {
        $version = python3 --version 2>&1
        Write-Host "  Found: $version" -ForegroundColor Green
        $pythonCmd = "python3"
    } catch {
        Write-Host "  Python not found. Install from:" -ForegroundColor Red
        Write-Host "  https://www.python.org/downloads/" -ForegroundColor White
        Write-Host "  (Check 'Add Python to PATH' during install)" -ForegroundColor White
        Write-Host ""
        Write-Host "  After installing Python, run this script again." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# ─── Step 2: Create Install Directory ───
Write-Host "`n[2/5] Creating install directory..." -ForegroundColor Yellow
New-Item -Path $InstallPath -ItemType Directory -Force | Out-Null
Write-Host "  Created: $InstallPath" -ForegroundColor Green

# ─── Step 3: Copy Server Files ───
Write-Host "`n[3/5] Copying server files..." -ForegroundColor Yellow
$serverSource = Join-Path $PSScriptRoot ".." "server"
if (Test-Path $serverSource) {
    Copy-Item -Path "$serverSource\*" -Destination $InstallPath -Recurse -Force
    Write-Host "  Server files copied" -ForegroundColor Green
} else {
    Write-Host "  Downloading from GitHub..." -ForegroundColor Yellow
    $zipUrl = "https://github.com/codeforge/codeforge/archive/refs/heads/main.zip"
    $zipPath = "$env:TEMP\codeforge.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath "$env:TEMP\codeforge-extract" -Force
    Copy-Item -Path "$env:TEMP\codeforge-extract\codeforge-main\server\*" -Destination $InstallPath -Recurse -Force
    Remove-Item $zipPath -Force
    Remove-Item "$env:TEMP\codeforge-extract" -Recurse -Force
    Write-Host "  Server downloaded and copied" -ForegroundColor Green
}

# ─── Step 4: Install Python Dependencies ───
Write-Host "`n[4/5] Installing dependencies..." -ForegroundColor Yellow

Push-Location $InstallPath
try {
    # Create virtual environment
    & $pythonCmd -m venv venv
    Write-Host "  Virtual environment created" -ForegroundColor Green
    
    # Activate and install
    $activatePath = Join-Path $InstallPath "venv\Scripts\Activate.ps1"
    . $activatePath
    
    pip install --upgrade pip | Out-Null
    pip install -r requirements.txt | Out-Null
    Write-Host "  Dependencies installed" -ForegroundColor Green
    
    # Install llama-cpp-python (pre-built)
    pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu | Out-Null
    Write-Host "  AI engine installed" -ForegroundColor Green
    
    deactivate
} finally {
    Pop-Location
}

# ─── Step 5: Download Model ───
Write-Host "`n[5/5] Setting up AI model..." -ForegroundColor Yellow

$modelDir = Join-Path $InstallPath "models"
New-Item -Path $modelDir -ItemType Directory -Force | Out-Null

if (-not $NoModel) {
    $modelUrl = switch ($Model) {
        "qwen-1.5b" { "https://huggingface.co/bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-Coder-1.5B-Instruct-Q4_K_M.gguf" }
        "deepseek-1.3b" { "https://huggingface.co/bartowski/DeepSeek-Coder-1.3B-Instruct-GGUF/resolve/main/DeepSeek-Coder-1.3B-Instruct-Q4_K_M.gguf" }
        default { $Model }
    }
    
    $modelName = Split-Path $modelUrl -Leaf
    $modelPath = Join-Path $modelDir $modelName
    
    if (Test-Path $modelPath) {
        Write-Host "  Model already exists: $modelName" -ForegroundColor Green
    } else {
        Write-Host "  Downloading model (this may take a few minutes)..." -ForegroundColor Yellow
        Write-Host "  URL: $modelUrl" -ForegroundColor Gray
        
        try {
            Invoke-WebRequest -Uri $modelUrl -OutFile $modelPath
            $size = (Get-Item $modelPath).Length / 1MB
            Write-Host "  Model downloaded: $([math]::Round($size)) MB" -ForegroundColor Green
        } catch {
            Write-Host "  Download failed. You can download a model manually later." -ForegroundColor Yellow
            Write-Host "  Place .gguf files in: $modelDir" -ForegroundColor White
        }
    }
} else {
    Write-Host "  Skipped (--NoModel flag)" -ForegroundColor Yellow
    Write-Host "  Download models manually to: $modelDir" -ForegroundColor White
}

# ─── Create Start Server Shortcut ───
Write-Host "`nCreating shortcuts..." -ForegroundColor Yellow

$startScript = @"
@echo off
cd /d $InstallPath
call venv\Scripts\activate
echo Starting CodeForge Server...
echo Server will be available at http://localhost:8000
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
"@

$startScriptPath = Join-Path $InstallPath "Start Server.bat"
$startScript | Out-File -FilePath $startScriptPath -Encoding ASCII

# Create desktop shortcut
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "CodeForge Server.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $startScriptPath
$Shortcut.WorkingDirectory = $InstallPath
$Shortcut.IconLocation = Join-Path $InstallPath "assets\icon.ico"
$Shortcut.Save()

Write-Host "  Desktop shortcut created" -ForegroundColor Green

# ─── Done ───
Write-Host @"

============================================
   Installation Complete!
============================================

Your CodeForge server is ready!

Location: $InstallPath
Start:    Double-click "CodeForge Server" on your desktop
          Or run: $startScriptPath

Next Steps:
1. Start the server (double-click desktop icon)
2. Install VS Code extension from Marketplace
3. Extension auto-discovers the server

============================================
"@ -ForegroundColor Green

Read-Host "Press Enter to finish"