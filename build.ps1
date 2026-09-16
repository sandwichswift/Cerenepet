param([switch]$SingleFile)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$petPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $petPython)) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 环境创建失败' }
    & $petPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw '依赖安装失败' }
}
$petBundleMode = '--onedir'
if ($SingleFile) { $petBundleMode = '--onefile' }
$petBuildArgs = @('-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed',
    $petBundleMode, '--name', 'CyrenePet', '--icon', 'assets\pet.ico',
    '--exclude-module', 'PyQt5', '--exclude-module', 'PyQt6')
foreach ($petSprite in 'idle.png', 'happy.png', 'sleep.png', 'walk.png') {
    $petBuildArgs += @('--add-data', "assets\$petSprite;assets")
}
& $petPython @petBuildArgs pet.py
if ($LASTEXITCODE -ne 0) { throw '打包失败' }
if ($SingleFile) {
    Write-Host 'Build complete: dist\CyrenePet.exe (standalone single file)'
} else {
    Write-Host 'Build complete: dist\CyrenePet\CyrenePet.exe'
}
