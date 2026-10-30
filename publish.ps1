# Push the reports stored on this machine to GitHub, where the workflow deploys them.
# Run from the project folder:   .\publish.ps1
# Leave the password empty for the open site. If the repository has a PANEL_PASSWORD
# secret, enter the same value here so the files are encrypted the same way.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$git = "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
if (-not (Test-Path $git)) { $git = "git" }

$sec = Read-Host -AsSecureString "Panel password (press Enter for none)"
$env:PANEL_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))

python backend/build_static.py --apply
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $git add -A data incoming ops
& $git commit -m "publish: reports from local machine"
& $git push origin main
Write-Host ""
Write-Host "Pushed. GitHub Actions now rebuilds the site (about 2 minutes)."
