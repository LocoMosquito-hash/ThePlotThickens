# PowerShell script to run Ren'Py API tests
# This handles Windows-specific path and import issues

Write-Host "🚀 Starting Ren'Py API Tests (PowerShell)" -ForegroundColor Green

# Navigate to the correct directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "📁 Current directory: $(Get-Location)" -ForegroundColor Cyan

# Try the fixed test script first
Write-Host "`n🔧 Running main test script..." -ForegroundColor Yellow
try {
    python test_renpy_api.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Main test completed successfully!" -ForegroundColor Green
        exit 0
    }
}
catch {
    Write-Host "❌ Main test script failed: $($_.Exception.Message)" -ForegroundColor Red
}

# If that fails, try the alternative runner
Write-Host "`n🔄 Trying alternative test runner..." -ForegroundColor Yellow
try {
    python run_test.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Alternative test completed successfully!" -ForegroundColor Green
        exit 0
    }
}
catch {
    Write-Host "❌ Alternative test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# If both fail, try running from parent directory
Write-Host "`n🔄 Trying from parent directory..." -ForegroundColor Yellow
try {
    Set-Location ..
    python -m renpy-source-api.test_renpy_api
}
catch {
    Write-Host "❌ Module execution failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n❌ All test methods failed. Check Python installation and paths." -ForegroundColor Red
exit 1 