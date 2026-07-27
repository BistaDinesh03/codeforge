<#
.SYNOPSIS
    CodeForge CLI - Main entry point
.DESCRIPTION
    One command for everything.
    Usage: .\scripts\codeforge.ps1 [command]

    Commands:
      setup     - Install everything needed for CodeForge
      start     - Show instructions to start phone server
      connect   - Connect VS Code to Android via ADB
      status    - Check connection status
      help      - Show this help message
#>

param(
    [Parameter(Position = 0)]
    [string]$Command = "help"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Show-Help {
    Write-Host @"
CodeForge CLI

Usage: .\scripts\codeforge.ps1 [command]

Commands:
  setup     - Install everything needed (Windows + phone instructions)
  connect   - Connect to Android device via ADB
  status    - Check if phone is connected and server is running
  start     - Instructions to start the phone server
  help      - Show this help message

Examples:
  .\scripts\codeforge.ps1 setup
  .\scripts\codeforge.ps1 connect
  .\scripts\codeforge.ps1 status

"@ -ForegroundColor Cyan
}

function Invoke-Setup {
    Write-Host "Starting CodeForge setup..." -ForegroundColor Cyan
    & "$ScriptDir\setup-windows.ps1"
}

function Invoke-Connect {
    Write-Host "Connecting to Android..." -ForegroundColor Yellow
    
    try {
        $adbVersion = (adb version | Select-Object -First 1)
        Write-Host "  [OK] ADB found" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] ADB not found. Run 'codeforge setup' first." -ForegroundColor Red
        return
    }

    $devices = adb devices 2>&1
    if ($devices -notmatch "device\s*$") {
        Write-Host "  [FAIL] No device connected. Plug in phone via USB." -ForegroundColor Red
        Write-Host "    Make sure USB Debugging is enabled." -ForegroundColor Yellow
        return
    }
    Write-Host "  [OK] Device found" -ForegroundColor Green

    adb forward tcp:8000 tcp:8000
    Write-Host "  [OK] Port 8000 forwarded" -ForegroundColor Green

    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5
        $json = $response.Content | ConvertFrom-Json
        if ($json.status -eq "healthy") {
            Write-Host "  [OK] Backend is healthy!" -ForegroundColor Green
            Write-Host ""
            Write-Host "CodeForge is ready! Open VS Code and run:" -ForegroundColor Cyan
            Write-Host "  Ctrl+Shift+P -> CodeForge: Open Chat" -ForegroundColor White
        }
    } catch {
        Write-Host "  [WARN] Port forwarded, but backend not responding." -ForegroundColor Yellow
        Write-Host "    Start the server on your phone first:" -ForegroundColor White
        Write-Host "    cd ~/codeforge/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
    }
}

function Invoke-Status {
    Write-Host "CodeForge Status" -ForegroundColor Cyan
    Write-Host "================" -ForegroundColor Cyan
    
    try {
        $adbVersion = (adb version | Select-Object -First 1)
        Write-Host "ADB:       [OK] Installed" -ForegroundColor Green
    } catch {
        Write-Host "ADB:       [FAIL] Not found" -ForegroundColor Red
        return
    }

    $devices = adb devices 2>&1
    if ($devices -match "device\s*$") {
        $deviceLine = ($devices -split '\n' | Select-String "device$").ToString().Trim()
        Write-Host "Device:    [OK] $deviceLine" -ForegroundColor Green
    } else {
        Write-Host "Device:    [FAIL] Not connected" -ForegroundColor Red
        return
    }

    $forwards = adb forward --list 2>&1
    if ($forwards -match "tcp:8000") {
        Write-Host "Port:      [OK] 8000 forwarded" -ForegroundColor Green
    } else {
        Write-Host "Port:      [FAIL] Not forwarded. Run 'codeforge connect'" -ForegroundColor Yellow
        return
    }

    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 3
        $json = $response.Content | ConvertFrom-Json
        Write-Host "Backend:   [OK] Healthy (v$($json.version))" -ForegroundColor Green
        Write-Host "Device:    $($json.device)" -ForegroundColor Green
    } catch {
        Write-Host "Backend:   [FAIL] Not responding" -ForegroundColor Red
        Write-Host "           Start server on phone: uvicorn app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor Yellow
    }
}

switch ($Command.ToLower()) {
    "setup"   { Invoke-Setup }
    "connect" { Invoke-Connect }
    "status"  { Invoke-Status }
    "start"   {
        Write-Host "To start the server on your Android phone:" -ForegroundColor Cyan
        Write-Host "  1. Open Termux" -ForegroundColor White
        Write-Host "  2. Run: cd ~/codeforge/backend" -ForegroundColor White
        Write-Host "  3. Run: uvicorn app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
        Write-Host ""
        Write-Host "Then on Windows: .\scripts\codeforge.ps1 connect" -ForegroundColor White
    }
    default    { Show-Help }
}