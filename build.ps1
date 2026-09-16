$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$petPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $petPython)) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 环境创建失败' }
    & $petPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw '依赖安装失败' }
}
& $petPython -m PyInstaller --noconfirm --clean --windowed --onedir --name CyrenePet --icon assets\pet.ico --add-data 'assets;assets' --exclude-module PyQt5 --exclude-module PyQt6 pet.py
if ($LASTEXITCODE -ne 0) { throw '打包失败' }
Write-Host '打包完成：dist\CyrenePet\CyrenePet.exe'
