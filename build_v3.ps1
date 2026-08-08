param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "== FNAF Save Manager v3 build ==" -ForegroundColor Cyan
Write-Host "Python: $(python --version)"
Write-Host "PyInstaller: $(pyinstaller --version)"

if ($Clean) {
    Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist
}

Write-Host "Building EXE..." -ForegroundColor Cyan
python -m PyInstaller --noconfirm --clean fnaf_save.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build FAILED." -ForegroundColor Red
    exit 1
}

$exe = Join-Path $Root "dist\fnaf_save_v3.exe"
if (Test-Path $exe) {
    $size = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host "Build OK: $exe ($size MB)" -ForegroundColor Green
} else {
    Write-Host "EXE not found after build." -ForegroundColor Red
    exit 1
}