<#
.SYNOPSIS
    CodeForge Windows Setup Script
.DESCRIPTION
    Installs and configures everything needed for CodeForge on Windows.
    Run: .\scripts\setup-windows.ps1
#>

param(
    [switch]$SkipAdbCheck,
    [switch]$SkipNodeCheck
)

Write-Host @"
========================================
   CodeForge Windows Setup
========================================
"@ -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# ──────────────────────────────────────
# Step 1: Check PowerShell version
# ──────────────────────────────────────
Write-Host "`n[1/6] Checking PowerShell version..." -ForegroundColor Yellow
$psVersion = $PSVersionTable.PSVersion
if ($psVersion.Major -lt 5) {
    Write-Host "ERROR: PowerShell 5.0+ required. You have $psVersion" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ PowerShell $psVersion" -ForegroundColor Green

# ──────────────────────────────────────
# Step 2: Check/Install Node.js
# ──────────────────────────────────────
if (-not $SkipNodeCheck) {
    Write-Host "`n[2/6] Checking Node.js..." -ForegroundColor Yellow
    $nodeInstalled = $null
    try {
        $nodeInstalled = (Get-Command node -ErrorAction SilentlyContinue)
    } catch {}

    if ($nodeInstalled) {
        $nodeVersion = (node --version)
        Write-Host "  ✓ Node.js $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "  Node.js not found. Installing..." -ForegroundColor Yellow
        winget install OpenJS.NodeJS.LTS --silent
        Write-Host "  ✓ Node.js installed. Please restart your terminal after setup." -ForegroundColor Green
    }

    # Check npm
    try {
        $npmVersion = (npm --version)
        Write-Host "  ✓ npm $npmVersion" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ npm not found (should come with Node.js)" -ForegroundColor Yellow
    }
}

# ──────────────────────────────────────
# Step 3: Check/Install Git
# ──────────────────────────────────────
Write-Host "`n[3/6] Checking Git..." -ForegroundColor Yellow
$gitInstalled = $null
try {
    $gitInstalled = (Get-Command git -ErrorAction SilentlyContinue)
} catch {}

if ($gitInstalled) {
    $gitVersion = (git --version)
    Write-Host "  ✓ $gitVersion" -ForegroundColor Green
} else {
    Write-Host "  Git not found. Installing..." -ForegroundColor Yellow
    winget install Git.Git --silent
    Write-Host "  ✓ Git installed. Please restart your terminal after setup." -ForegroundColor Green
}

# ──────────────────────────────────────
# Step 4: Check/Install ADB
# ──────────────────────────────────────
if (-not $SkipAdbCheck) {
    Write-Host "`n[4/6] Checking ADB..." -ForegroundColor Yellow
    $adbInstalled = $null
    try {
        $adbInstalled = (Get-Command adb -ErrorAction SilentlyContinue)
    } catch {}

    if ($adbInstalled) {
        $adbVersion = (adb version | Select-Object -First 1)
        Write-Host "  ✓ $adbVersion" -ForegroundColor Green
    } else {
        Write-Host "  ADB not found. Installing..." -ForegroundColor Yellow
        winget install Google.PlatformTools --silent
        Write-Host "  ✓ ADB installed. Please restart your terminal after setup." -ForegroundColor Green
    }
}

# ──────────────────────────────────────
# Step 5: Install VS Code Extension Dependencies
# ──────────────────────────────────────
Write-Host "`n[5/6] Installing VS Code extension dependencies..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot\..\vscode-extension"
npm install
Set-Location ..
Write-Host "  ✓ Extension dependencies installed" -ForegroundColor Green

# ──────────────────────────────────────
# Step 6: Check Android Connection
# ──────────────────────────────────────
Write-Host "`n[6/6] Checking Android connection..." -ForegroundColor Yellow
$devices = adb devices 2>$null
if ($devices -match "device\s*$") {
    Write-Host "  ✓ Android device connected!" -ForegroundColor Green
    
    # Check if Termux has our backend
    Write-Host "`n  Checking phone setup..." -ForegroundColor Yellow
    Write-Host "  Run this on your Android phone (Termux):" -ForegroundColor Cyan
    Write-Host "    curl -sL https://raw.githubusercontent.com/codeforge/install/main/setup-android.sh | bash" -ForegroundColor White
} else {
    Write-Host "  ⚠ No Android device detected." -ForegroundColor Yellow
    Write-Host "    1. Enable USB Debugging on your phone" -ForegroundColor White
    Write-Host "    2. Connect via USB cable" -ForegroundColor White
    Write-Host "    3. Run this script again" -ForegroundColor White
}

# ──────────────────────────────────────
# Summary
# ──────────────────────────────────────
Write-Host @"

========================================
   Setup Complete!
========================================

Next steps:
  1. Restart your terminal
  2. On your Android phone, run the Termux setup script
  3. In VS Code: Ctrl+Shift+P → 'CodeForge: Connect to Android'

"@ -ForegroundColor Green