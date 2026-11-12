$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

Write-Host ''
Write-Host 'OPENROUTER ARCHIVE STUDIO - INSTALLER' -ForegroundColor Cyan
Write-Host 'This installs Python packages into a private .venv in this folder.'
Write-Host 'It does not modify your system Python installation.'
Write-Host ''

$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue

if ($pythonLauncher) {
    $pythonExe = $pythonLauncher.Source
    $pythonArgs = @('-3')
} elseif ($pythonCommand) {
    $pythonExe = $pythonCommand.Source
    $pythonArgs = @()
} else {
    throw 'Python 3.10 or newer was not found. Install Python from https://www.python.org/downloads/windows/ and select "Add python.exe to PATH", then run this installer again.'
}

& $pythonExe @pythonArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw 'Python 3.10 or newer is required.'
}

if (-not (Test-Path '.venv/Scripts/python.exe')) {
    & $pythonExe @pythonArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the private Python environment.' }
}

$venvPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Could not update pip.' }

& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }

Write-Host ''
Write-Host 'Installation complete. Starting OpenRouter Archive Studio...' -ForegroundColor Green
& $venvPython OpenRouter_Translate_Viewer.py
if ($LASTEXITCODE -ne 0) { throw 'The application exited with an error.' }
