# Encrypt the reports stored on this machine with the panel password and push them to GitHub.
# Run from the project folder:   .\publish.ps1
# The password must be the same value as the PANEL_PASSWORD secret of the GitHub repository.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$git = "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
if (-not (Test-Path $git)) { $git = "git" }

$sec = Read-Host -AsSecureString "Panel password (same as the PANEL_PASSWORD secret on GitHub)"
$env:PANEL_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
if (-not $env:PANEL_PASSWORD) { Write-Host "No password given."; exit 1 }

python backend/build_static.py --apply
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $git add -A data incoming ops
& $git commit -m "publish: encrypted reports from local machine"
& $git push origin main
Write-Host ""
Write-Host "Pushed. GitHub Actions now rebuilds the site (about 2 minutes)."
