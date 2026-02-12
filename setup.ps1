# PowerShell setup script for CoRec Tracker

Write-Host "CoRec Tracker - Setup Script" -ForegroundColor Cyan
Write-Host "=================================================="

# Check if Python is installed
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
$pythonCheck = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCheck) {
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "Python found: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "Python command found but version check failed" -ForegroundColor Yellow
    }
} else {
    Write-Host "Python not found!" -ForegroundColor Red
    Write-Host "`nPlease install Python first:" -ForegroundColor Yellow
    Write-Host "1. Download from https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "2. During installation, check 'Add Python to PATH'" -ForegroundColor White
    Write-Host "3. Restart PowerShell and run this script again" -ForegroundColor White
    exit 1
}

# Check if pip is available
Write-Host "`nChecking pip..." -ForegroundColor Yellow
try {
    $pipVersion = python -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "pip found: $pipVersion" -ForegroundColor Green
    } else {
        Write-Host "pip not found, installing..." -ForegroundColor Yellow
        python -m ensurepip --upgrade
    }
} catch {
    Write-Host "pip check failed" -ForegroundColor Yellow
}

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    Write-Host "You may need to install Python first. See SETUP.md for details." -ForegroundColor Yellow
    exit 1
}

# Check Chrome installation
Write-Host "`nChecking Chrome browser..." -ForegroundColor Yellow
$chromePaths = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)

$chromeFound = $false
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        Write-Host "Chrome found at: $path" -ForegroundColor Green
        $chromeFound = $true
        break
    }
}

if (-not $chromeFound) {
    Write-Host "Chrome not found in common locations" -ForegroundColor Yellow
    Write-Host "Make sure Chrome is installed: https://www.google.com/chrome/" -ForegroundColor White
}

# Summary
Write-Host "`n=================================================="
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Test the scraper: python test_scraper.py" -ForegroundColor White
Write-Host "2. Start collecting data: python collect_data.py" -ForegroundColor White
Write-Host "3. Analyze data: python analyze.py --facility `"CoRec`"" -ForegroundColor White
