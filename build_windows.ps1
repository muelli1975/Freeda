param([switch]$TestBuild)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Venv = Join-Path $Root ".venv-build"
$Build = Join-Path $Root "build"
$Dist = Join-Path $Root "dist"
$Release = Join-Path $Root "release"

$PythonCommand = Get-Command python -ErrorAction Stop
if (-not (Test-Path (Join-Path $Venv "Scripts\python.exe"))) {
    & $PythonCommand.Source -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw "Build environment creation failed." }
}
$Python = Join-Path $Venv "Scripts\python.exe"
$Version = (& $Python -c "from freeda import __version__; print(__version__)").Trim()
$DisplayVersion = $Version -replace '\.0$', ''
$PackageName = "Freeda_${DisplayVersion}_Windows_x64"
if ($TestBuild) { $PackageName += "_Testbuild" }
$Package = Join-Path $Release $PackageName
$Zip = Join-Path $Release "$PackageName.zip"

& $Python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "Build dependency installation failed." }
& $Python scripts/prepare_exiftool.py
if ($LASTEXITCODE -ne 0) { throw "ExifTool preparation failed." }
& $Python -m unittest discover -s tests -p "test_*.py"
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed." }

& $Python -m compileall -q Freeda.py freeda tests
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed." }

& $Python -m PyInstaller --noconfirm --clean Freeda.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

$Program = Join-Path $Dist "Freeda"
$Exe = Join-Path $Program "Freeda.exe"
Copy-Item -Recurse -Force (Join-Path $Root "tools") $Program
if (-not (Test-Path $Exe)) {
    throw "PyInstaller did not create Freeda.exe"
}

New-Item -ItemType Directory -Force $Package | Out-Null
Copy-Item -Force $Exe (Join-Path $Package "Freeda.exe")
Copy-Item -Recurse -Force (Join-Path $Program "_internal") $Package
Copy-Item -Recurse -Force (Join-Path $Program "tools") $Package
Copy-Item -Force (Join-Path $Root "README.md") (Join-Path $Package "README.md")
Copy-Item -Force (Join-Path $Root "README_EN.md") (Join-Path $Package "README_EN.md")
Copy-Item -Force (Join-Path $Root "README_DE.md") (Join-Path $Package "README_DE.md")
Copy-Item -Recurse -Force (Join-Path $Root "docs") $Package
Copy-Item -Force (Join-Path $Root "QUICKSTART.md") (Join-Path $Package "QUICKSTART.md")
Copy-Item -Force (Join-Path $Root "RELEASE_NOTES_1.2.md") (Join-Path $Package "RELEASE_NOTES_1.2.md")
Copy-Item -Force (Join-Path $Root "THIRD_PARTY_NOTICES.md") (Join-Path $Package "THIRD_PARTY_NOTICES.md")
Copy-Item -Recurse -Force (Join-Path $Root "licenses") $Package
Copy-Item -Force (Join-Path $Root "LICENSE") (Join-Path $Package "LICENSE")

& $Python scripts/prepare_release.py $Package
if ($LASTEXITCODE -ne 0) { throw "Source/license snapshot failed." }

Compress-Archive -Path $Package -DestinationPath $Zip -CompressionLevel Optimal -Force
$Hash = (Get-FileHash -Algorithm SHA256 $Zip).Hash.ToLowerInvariant()
$ChecksumName = if ($TestBuild) { "${PackageName}_SHA256.txt" } else { "SHA256SUMS.txt" }
"$Hash  $PackageName.zip" | Set-Content -Encoding ASCII (Join-Path $Release $ChecksumName)

Write-Host ""
Write-Host "Freeda release build created:"
Write-Host $Zip
Write-Host "SHA256:" $Hash
