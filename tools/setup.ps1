param([ValidateSet('app','pipeline','mcp','build','all')][string]$Environment = 'app')
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Set-Location (Split-Path $PSScriptRoot -Parent)
$targets = @{
    app = @('.venv', 'requirements-lock-windows.txt')
    build = @('.venv', 'requirements-build-lock-windows.txt')
    pipeline = @('.venv-pipeline', 'art-pipeline/requirements-lock-windows.txt')
    mcp = @('.venv-mcp', 'tools/xingai_mcp/requirements-lock-windows.txt')
}
$selected = if ($Environment -eq 'all') { @('build','pipeline','mcp') } else { @($Environment) }
foreach ($name in $selected) {
    $venv = $targets[$name][0]
    $lock = $targets[$name][1]
    $python = "$venv/Scripts/python.exe"
    if (!(Test-Path $python)) {
        py -3.11 -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed' }
    }
    & $python -c 'import sys; assert sys.version_info[:2] == (3, 11), "Python 3.11 required"'
    if ($LASTEXITCODE -ne 0) { throw 'Incompatible existing virtual environment' }
    & $python -m pip install -r $lock
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed: $name" }
    & $python -m pip check
    if ($LASTEXITCODE -ne 0) { throw "Dependency consistency failed: $name" }
    if ($name -in @('app','build')) { & $python tools/check_project.py }
    elseif ($name -eq 'mcp') { & $python -m unittest discover -s tools/xingai_mcp -p 'test_image_routing.py' }
    else { & $python -c 'from openai import OpenAI; from PIL import Image; print("Pipeline imports: PASS")' }
    if ($LASTEXITCODE -ne 0) { throw "Checks failed: $name" }
}
