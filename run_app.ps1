Set-Location -Path $PSScriptRoot
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  ANTICIPATORY COMMERCE AI AGENT - STREAMLIT LAUNCHER" -ForegroundColor Cyan
Write-Host "  Project Directory: $PWD" -ForegroundColor Gray
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
if (Test-Path "$PSScriptRoot\.venv\Scripts\streamlit.exe") {
    Write-Host "[OK] Virtual environment detected." -ForegroundColor Green
    Write-Host "[INFO] Launching Streamlit web application on http://localhost:8501 ..." -ForegroundColor Yellow
    & "$PSScriptRoot\.venv\Scripts\streamlit.exe" run "$PSScriptRoot\app.py" --server.port 8501
} else {
    Write-Host "[ERROR] .venv not found in $PSScriptRoot" -ForegroundColor Red
}
