[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$SourceDirectory,

    [ValidateRange(1, 16)]
    [int]$Jobs = 2,

    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-Command {
    param([Parameter(Mandatory)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory)][string]$Command,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$FailureMessage
    )

    Write-Host "> $Command $($Arguments -join ' ')"
    & $Command @Arguments

    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage Exit code: $LASTEXITCODE."
    }
}

Assert-Command -Name "pixi"
Assert-Command -Name "cmake"

$resolvedSource = [System.IO.Path]::GetFullPath($SourceDirectory)
if (-not (Test-Path -LiteralPath (Join-Path $resolvedSource "pixi.toml"))) {
    throw "The source directory does not contain pixi.toml: $resolvedSource"
}

$environmentRoot = Join-Path $resolvedSource ".pixi/envs/default"
$freeCADExecutable = Join-Path $environmentRoot "Library/bin/FreeCAD.exe"
$freeCADCommand = Join-Path $environmentRoot "Library/bin/FreeCADCmd.exe"

Push-Location $resolvedSource
try {
    Invoke-CheckedCommand `
        -Command "pixi" `
        -Arguments @("install", "--frozen") `
        -FailureMessage "Pixi dependency installation failed."

    Invoke-CheckedCommand `
        -Command "pixi" `
        -Arguments @("run", "configure-release") `
        -FailureMessage "FreeCAD Release configuration failed."

    Invoke-CheckedCommand `
        -Command "pixi" `
        -Arguments @("run", "build-release", "-j", $Jobs.ToString()) `
        -FailureMessage "FreeCAD Release compilation failed."

    Invoke-CheckedCommand `
        -Command "pixi" `
        -Arguments @("run", "install-release") `
        -FailureMessage "FreeCAD Release installation failed."
}
finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $freeCADExecutable)) {
    throw "Compilation completed without FreeCAD.exe at: $freeCADExecutable"
}

if (-not (Test-Path -LiteralPath $freeCADCommand)) {
    throw "Compilation completed without FreeCADCmd.exe at: $freeCADCommand"
}

if (-not $SkipSmokeTest) {
    $previousPath = $env:PATH
    $previousPythonHome = $env:PYTHONHOME

    try {
        $env:PATH = "$(Join-Path $environmentRoot 'Library/bin');$environmentRoot;$(Join-Path $environmentRoot 'Scripts');$previousPath"
        $env:PYTHONHOME = $environmentRoot

        Write-Host "Running FreeCADCmd smoke test..."
        & $freeCADCommand --version

        if ($LASTEXITCODE -ne 0) {
            throw "FreeCADCmd smoke test failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        $env:PATH = $previousPath
        $env:PYTHONHOME = $previousPythonHome
    }
}

Write-Host "FreeCAD Windows Release build completed successfully."
Write-Host "Executable: $freeCADExecutable"
Write-Host "Environment: $environmentRoot"
