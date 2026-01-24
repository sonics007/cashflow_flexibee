# Cashflow Dashboard - Windows Installer
# PowerShell Script for Windows 10/11
#
# Usage: Run as Administrator
#   powershell -ExecutionPolicy Bypass -File install-windows.ps1

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Clear-Host
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Cashflow Dashboard Installer" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "This script will automatically:" -ForegroundColor Blue
Write-Host "  * Install Python 3.11 (if not installed)"
Write-Host "  * Install Git (if not installed)"
Write-Host "  * Clone the repository from GitHub"
Write-Host "  * Setup virtual environment"
Write-Host "  * Install Python packages"
Write-Host "  * Create Windows Service (NSSM)"
Write-Host "  * Setup FlexiBee integration (optional)"
Write-Host "  * Start the application"
Write-Host ""

# Configuration
Write-Host "Installation Configuration:" -ForegroundColor Yellow
$installDir = Read-Host "Installation directory [default: C:\cashflow]"
if ([string]::IsNullOrWhiteSpace($installDir)) {
    $installDir = "C:\cashflow"
}

$port = Read-Host "Application port [default: 8887]"
if ([string]::IsNullOrWhiteSpace($port)) {
    $port = "8887"
}

Write-Host ""
Write-Host "FlexiBee Configuration (optional):" -ForegroundColor Yellow
$configureFlexiBee = Read-Host "Configure FlexiBee now? (y/n) [default: n]"

if ($configureFlexiBee -eq "y" -or $configureFlexiBee -eq "Y") {
    Write-Host ""
    Write-Host "Enter FlexiBee connection details:"
    $fbHost = Read-Host "  Server URL (e.g., https://demo.flexibee.eu:5434)"
    $fbCompany = Read-Host "  Company Code (e.g., demo_sro)"
    $fbUser = Read-Host "  API Username"
    $fbPasswordSecure = Read-Host "  API Password" -AsSecureString
    $fbPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($fbPasswordSecure))
    $fbEnabled = Read-Host "  Enable automatic hourly sync? (y/n) [default: n]"
    
    if ($fbEnabled -eq "y" -or $fbEnabled -eq "Y") {
        $fbEnabledBool = "true"
    } else {
        $fbEnabledBool = "false"
    }
} else {
    $fbHost = ""
    $fbCompany = ""
    $fbUser = ""
    $fbPassword = ""
    $fbEnabledBool = "false"
}

# Summary
Write-Host ""
Write-Host "Installation Summary:" -ForegroundColor Yellow
Write-Host "  Directory: $installDir"
Write-Host "  Port: $port"
if ($fbHost) {
    Write-Host "  FlexiBee: Enabled ($fbHost)"
} else {
    Write-Host "  FlexiBee: Not configured"
}
Write-Host ""
$confirm = Read-Host "Continue? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Installation cancelled." -ForegroundColor Red
    exit 0
}

# Step 1: Install Python
Write-Host ""
Write-Host "==========================================" -ForegroundColor Blue
Write-Host "  Step 1/7: Installing Python 3.11" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue

$pythonInstalled = $false
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3") {
        Write-Host "Python already installed: $pythonVersion" -ForegroundColor Green
        $pythonInstalled = $true
    }
} catch {}

if (-not $pythonInstalled) {
    Write-Host "Downloading Python 3.11..."
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-installer.exe"
    
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
    
    Write-Host "Installing Python 3.11..."
    Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
    
    # Refresh PATH properly
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "Python 3.11 installed" -ForegroundColor Green
}

# Step 2: Install Git
Write-Host ""
Write-Host "==========================================" -ForegroundColor Blue
Write-Host "  Step 2/7: Installing Git" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue

$gitInstalled = $false
try {
    $gitVersion = git --version 2>&1
    if ($gitVersion -match "git version") {
        Write-Host "Git already installed: $gitVersion" -ForegroundColor Green
        $gitInstalled = $true
    }
} catch {}

if (-not $gitInstalled) {
    Write-Host "Downloading Git..."
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    $gitInstaller = "$env:TEMP\git-installer.exe"
    
    Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller
    
    Write-Host "Installing Git..."
    Start-Process -FilePath $gitInstaller -ArgumentList "/VERYSILENT /NORESTART" -Wait
    
    # Refresh PATH properly
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "Git installed" -ForegroundColor Green
}

# Step 3: Clone Repository
Write-Host ""
Write-Host "==========================================" -ForegroundColor Blue
Write-Host "  Step 3/7: Cloning Repository" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue

if (Test-Path $installDir) {
    Write-Host "Directory $installDir already exists" -ForegroundColor Yellow
    $remove = Read-Host "Remove and reinstall? (y/n)"
    if ($remove -eq "y" -or $remove -eq "Y") {
        Remove-Item -Path $installDir -Recurse -Force
        Write-Host "Old installation removed" -ForegroundColor Green
    } else {
        Write-Host "Installation cancelled." -ForegroundColor Red
        exit 0
    }
}

Write-Host "Cloning from GitHub..."
git clone https://github.com/sonics007/cashflow_flexibee.git $installDir 2>&1 | Out-Null

Write-Host "Repository cloned to $installDir" -ForegroundColor Green

Set-Location $installDir

# Step 4: Create Virtual Environment
Write-Host ""
Write-Host "==========================================" -ForegroundColor Blue
Write-Host "  Step 4/7: Creating Virtual Environment" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue

python -m venv venv
Write-Host "Virtual environment created" -ForegroundColor Green

# Step 5: Install Python Packages
Write-Host ""
Write-Host "==========================================" -ForegroundColor Blue
Write-Host "  Step 5/7: Installing Python Packages" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue

& "$installDir\venv\Scripts\pip.exe" install --upgrade pip 2>&1 | Out-Null
& "$installDir\venv\Scripts\pip.exe" install flask pandas openpyxl werkzeug cryptography schedule 2>&1 | Out-Null

Write-Host "Python packages installed" -ForegroundColor Green

# Step 6: Create Data Directory and FlexiBee Config
Write-Host ""
Write-Host "==========================================" -ForegroundColor Blue
Write-Host "  Step 6/7: Creating Data Directory" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue

New-Item -ItemType Directory -Path "$installDir\data" -Force | Out-Null

if ($fbHost) {
    Write-Host "Creating FlexiBee configuration..."
    
    $pythonScript = @"
import json
import os
from flexibee_sync import PasswordEncryption

config = {
    'host': '$fbHost',
    'company': '$fbCompany',
    'user': '$fbUser',
    'password': PasswordEncryption.encrypt('$fbPassword'),
    'password_encrypted': True,
    'enabled': $fbEnabledBool,
    'last_sync': ''
}

os.makedirs('data', exist_ok=True)
with open('data/flexibee_config.json', 'w') as f:
    json.dump(config, f, indent=4)

print('FlexiBee config created')
"@
    
    $pythonScript | & "$installDir\venv\Scripts\python.exe" -
    Write-Host "FlexiBee configured" -ForegroundColor Green
}

Write-Host "Data directory ready" -ForegroundColor Green

# Step 7: Install NSSM and Create Windows Service
Write-Host ""
Write-Host "==========================================" -ForegroundColor Blue
Write-Host "  Step 7/7: Creating Windows Service" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue

# Download NSSM
$nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
$nssmZip = "$env:TEMP\nssm.zip"
$nssmDir = "$env:TEMP\nssm"

Write-Host "Downloading NSSM (Non-Sucking Service Manager)..."
Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
Expand-Archive -Path $nssmZip -DestinationPath $nssmDir -Force

$nssmExe = "$nssmDir\nssm-2.24\win64\nssm.exe"

# Remove existing service if exists
& $nssmExe stop CashflowDashboard 2>&1 | Out-Null
& $nssmExe remove CashflowDashboard confirm 2>&1 | Out-Null

# Install service
& $nssmExe install CashflowDashboard "$installDir\venv\Scripts\python.exe" "$installDir\app.py"
& $nssmExe set CashflowDashboard AppDirectory $installDir
& $nssmExe set CashflowDashboard AppEnvironmentExtra "PORT=$port"
& $nssmExe set CashflowDashboard DisplayName "Cashflow Dashboard"
& $nssmExe set CashflowDashboard Description "Cashflow Dashboard with FlexiBee Integration"
& $nssmExe set CashflowDashboard Start SERVICE_AUTO_START

# Start service
& $nssmExe start CashflowDashboard

Write-Host "Windows Service created and started" -ForegroundColor Green

# Add firewall rule
Write-Host "Adding firewall rule for port $port..."
New-NetFirewallRule -DisplayName "Cashflow Dashboard" -Direction Inbound -LocalPort $port -Protocol TCP -Action Allow -ErrorAction SilentlyContinue | Out-Null
Write-Host "Firewall rule added" -ForegroundColor Green

Start-Sleep -Seconds 2

# Final message
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "   Installation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access your Cashflow Dashboard at:" -ForegroundColor Cyan
Write-Host "  http://localhost:$port" -ForegroundColor Blue
Write-Host ""
Write-Host "Default Login:" -ForegroundColor Yellow
Write-Host "  Username: admin" -ForegroundColor Green
Write-Host "  Password: admin" -ForegroundColor Green
Write-Host "   CHANGE PASSWORD IMMEDIATELY!" -ForegroundColor Red
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Cyan
Write-Host "  $nssmExe status CashflowDashboard    # Check status"
Write-Host "  $nssmExe restart CashflowDashboard   # Restart"
Write-Host "  $nssmExe stop CashflowDashboard      # Stop"
Write-Host ""
Write-Host "Installation Details:" -ForegroundColor Cyan
Write-Host "  Directory: $installDir"
Write-Host "  Port: $port"
Write-Host "  Service: CashflowDashboard"
Write-Host ""
if ($fbHost) {
    Write-Host "FlexiBee is configured and ready!" -ForegroundColor Green
    Write-Host ""
}
Write-Host "Happy cash flowing!" -ForegroundColor Green
Write-Host ""
Write-Host "Press Enter to open the dashboard in your browser..."
Read-Host

Start-Process "http://localhost:$port"
