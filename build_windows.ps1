$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Venv = Join-Path $Root ".venv-build"
$Build = Join-Path $Root "build"
$Dist = Join-Path $Root "dist"
$Release = Join-Path $Root "release"

foreach ($Path in @($Venv, $Build, $Dist, $Release)) {
    if (Test-Path $Path) { Remove-Item -Recurse -Force $Path }
}

$PythonCommand = Get-Command python -ErrorAction Stop
& $PythonCommand.Source -m venv $Venv
$Python = Join-Path $Venv "Scripts\python.exe"

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements-build.txt
& $Python -m unittest discover -s tests -p "test_*.py"
& $Python -m compileall -q Freeda.py freeda tests
& $Python -m PyInstaller --noconfirm --clean Freeda.spec

$Exe = Join-Path $Dist "Freeda.exe"
if (-not (Test-Path $Exe)) {
    throw "PyInstaller did not create Freeda.exe"
}

New-Item -ItemType Directory -Force $Release | Out-Null
$Zip = Join-Path $Release "Freeda-dev-win64.zip"
Compress-Archive -Path $Exe -DestinationPath $Zip -CompressionLevel Optimal
$Hash = (Get-FileHash -Algorithm SHA256 $Zip).Hash.ToLowerInvariant()
"$Hash  Freeda-dev-win64.zip" | Set-Content -Encoding ASCII (Join-Path $Release "SHA256SUMS.txt")

Write-Host ""
Write-Host "Freeda build created:"
Write-Host $Zip
Write-Host "SHA256:" $Hash
