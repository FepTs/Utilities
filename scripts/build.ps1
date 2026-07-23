param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BuildEnvironment = Join-Path $ProjectRoot ".venv-build"

Push-Location $ProjectRoot
try {
    & $Python -m venv $BuildEnvironment
    $BuildPython = Join-Path $BuildEnvironment "Scripts\python.exe"
    & $BuildPython -m pip install --upgrade pip
    & $BuildPython -m pip install -r (Join-Path $ProjectRoot "requirements-build.txt")
    & $BuildPython -m PyInstaller --noconfirm --clean (Join-Path $ProjectRoot "YoloUtilities.spec")

    $Executable = Join-Path $ProjectRoot "dist\YoloUtilities.exe"
    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
        throw "构建失败：未生成 $Executable"
    }
    $SmokeTest = Start-Process -FilePath $Executable -ArgumentList "--smoke-test" -PassThru -Wait
    if ($SmokeTest.ExitCode -ne 0) {
        throw "构建失败：可执行文件未通过界面启动烟测。"
    }

    $SizeMb = [Math]::Round((Get-Item -LiteralPath $Executable).Length / 1MB, 2)
    Write-Output "构建完成：$Executable ($SizeMb MB)"
}
finally {
    Pop-Location
}
