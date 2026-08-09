param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$AppExe = "fnaf_save_v3.exe"
$SetupName = "FNAF Save Manager Setup.exe"
$InstallerDir = Join-Path $Root "installer"

Write-Host "== FNAF Save Manager Installer build ==" -ForegroundColor Cyan

if ($Clean) {
    Write-Host "Cleaning old installer output..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $InstallerDir "obj")
}

# 1) Make sure the app EXE exists
$distExe = Join-Path $Root "dist\$AppExe"
if (-not (Test-Path $distExe)) {
    Write-Host "ERROR: $AppExe not found in dist\. Build the app first (build_v3.ps1)." -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Force $InstallerDir | Out-Null

# 2) Embedded resources: app EXE, banner image, music, app icon
#    (copy to short, space-free names so csc.exe parses them cleanly)
$appEmbed   = Join-Path $InstallerDir "app.bin"
$banner     = Join-Path $Root "installer banner image.png"
$music      = Join-Path $Root "instaaller music.mp3"
$icon       = Join-Path $Root "favicon.ico"
foreach ($p in @($banner, $music, $icon)) {
    if (-not (Test-Path $p)) { Write-Host "WARNING: missing resource $p" -ForegroundColor Yellow }
}
Copy-Item -Force $distExe $appEmbed
$bannerEmbed = Join-Path $InstallerDir "banner.png"
$musicEmbed  = Join-Path $InstallerDir "music.mp3"
$iconEmbed   = Join-Path $InstallerDir "icon.ico"
Copy-Item -Force $banner $bannerEmbed
Copy-Item -Force $music  $musicEmbed
Copy-Item -Force $icon   $iconEmbed

# 4) Compile the C# installer with the .NET Framework compiler (csc.exe)
$csc = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path $csc)) { $csc = "$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe" }

$outTmp = Join-Path $InstallerDir "setup_tmp.exe"
$manifest = Join-Path $InstallerDir "app.manifest"
Write-Host "Compiling C# installer (csc.exe)..." -ForegroundColor Cyan
& $csc /nologo /target:winexe /optimize+ "/out:$outTmp" `
    /r:System.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:Microsoft.CSharp.dll `
    "/win32manifest:$manifest" `
    "/resource:$appEmbed,InstallerApp" `
    "/resource:$bannerEmbed,InstallerBanner" `
    "/resource:$musicEmbed,InstallerMusic" `
    "/resource:$iconEmbed,InstallerIcon" `
    (Join-Path $InstallerDir "Setup.cs")

if ($LASTEXITCODE -ne 0) {
    Write-Host "Installer compile FAILED." -ForegroundColor Red
    exit 1
}

$setup = Join-Path $InstallerDir $SetupName
Remove-Item -Force $setup -ErrorAction SilentlyContinue
Rename-Item -Force $outTmp $setup
Remove-Item -Force -ErrorAction SilentlyContinue $bannerEmbed, $musicEmbed, $iconEmbed, $appEmbed
Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $InstallerDir $AppExe)

if (Test-Path $setup) {
    $size = [math]::Round((Get-Item $setup).Length / 1MB, 1)
    Write-Host "Installer OK: $setup ($size MB)" -ForegroundColor Green
} else {
    Write-Host "Installer not found after compile." -ForegroundColor Red
    exit 1
}