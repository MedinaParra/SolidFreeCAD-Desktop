[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$SourceDirectory,

    [string]$OutputDirectory = "dist",

    [string]$ProductVersion = "0.1.0-alpha.1",

    [string]$FreeCADTag = "1.1.1",

    [switch]$SkipPortableSmokeTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-Command {
    param([Parameter(Mandatory)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

function Invoke-Robocopy {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )

    $excludedDirectories = @(
        "conda-meta",
        "include",
        "Library/include",
        "Library/lib/cmake",
        "Library/lib/pkgconfig",
        "Library/share/doc",
        "Library/share/info",
        "Library/share/man",
        "Lib/test",
        "Lib/tests",
        "__pycache__"
    )

    $arguments = @(
        $Source,
        $Destination,
        "/E",
        "/R:2",
        "/W:2",
        "/NFL",
        "/NDL",
        "/NJH",
        "/NJS",
        "/NP",
        "/XF",
        "*.lib",
        "*.a",
        "*.exp",
        "*.pdb",
        "*.pyc",
        "/XD"
    ) + $excludedDirectories

    & robocopy @arguments
    $exitCode = $LASTEXITCODE

    if ($exitCode -gt 7) {
        throw "Robocopy failed with exit code $exitCode."
    }
}

Assert-Command -Name "robocopy"
Assert-Command -Name "7z"
Assert-Command -Name "git"

$resolvedSource = [System.IO.Path]::GetFullPath($SourceDirectory)
$resolvedOutput = if ([System.IO.Path]::IsPathFullyQualified($OutputDirectory)) {
    [System.IO.Path]::GetFullPath($OutputDirectory)
}
else {
    [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputDirectory))
}

$environmentRoot = Join-Path $resolvedSource ".pixi/envs/default"
$sourceExecutable = Join-Path $environmentRoot "Library/bin/FreeCAD.exe"

if (-not (Test-Path -LiteralPath $sourceExecutable)) {
    throw "FreeCAD.exe was not found. Run Build-FreeCAD.ps1 first: $sourceExecutable"
}

New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null

$packageName = "SolidFreeCAD-$ProductVersion-FreeCAD-$FreeCADTag-Windows-x64-Portable-Baseline"
$stagingDirectory = Join-Path $resolvedOutput $packageName
$archivePath = Join-Path $resolvedOutput "$packageName.7z"
$checksumPath = "$archivePath.sha256"

if (Test-Path -LiteralPath $stagingDirectory) {
    Remove-Item -LiteralPath $stagingDirectory -Recurse -Force
}

if (Test-Path -LiteralPath $archivePath) {
    Remove-Item -LiteralPath $archivePath -Force
}

Write-Host "Creating portable runtime staging directory..."
Invoke-Robocopy -Source $environmentRoot -Destination $stagingDirectory

$launcher = @'
@echo off
setlocal
set "ROOT=%~dp0"
set "PATH=%ROOT%Library\bin;%ROOT%;%ROOT%Scripts;%PATH%"
set "PYTHONHOME=%ROOT%"
start "SolidFreeCAD Baseline" "%ROOT%Library\bin\FreeCAD.exe" %*
endlocal
'@

Set-Content `
    -LiteralPath (Join-Path $stagingDirectory "Start-SolidFreeCAD-Baseline.cmd") `
    -Value $launcher `
    -Encoding ascii

$readme = @"
SolidFreeCAD Windows portable baseline
======================================

SolidFreeCAD version: $ProductVersion
FreeCAD engine tag: $FreeCADTag
Platform: Windows x64

This package is the unmodified FreeCAD engine baseline used to validate the
Windows build and runtime before SolidFreeCAD branding and interface overlays
are applied.

Launch:
  Start-SolidFreeCAD-Baseline.cmd

Direct executable:
  Library\bin\FreeCAD.exe

The Ubuntu platform files and roadmap are not part of this Windows package and
remain preserved independently in the repository.
"@

Set-Content `
    -LiteralPath (Join-Path $stagingDirectory "README-BASELINE.txt") `
    -Value $readme `
    -Encoding utf8

$upstreamCommit = (& git -C $resolvedSource rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read the upstream FreeCAD commit."
}

$metadata = [ordered]@{
    product = "SolidFreeCAD Desktop"
    productVersion = $ProductVersion
    packageKind = "windows-portable-baseline"
    architecture = "x86_64"
    freecadTag = $FreeCADTag
    freecadCommit = $upstreamCommit
    createdUtc = [DateTime]::UtcNow.ToString("o")
    branded = $false
    notes = "Unmodified FreeCAD runtime baseline for Windows validation."
}

$metadata | ConvertTo-Json -Depth 5 | Set-Content `
    -LiteralPath (Join-Path $stagingDirectory "BUILD-METADATA.json") `
    -Encoding utf8

$portableExecutable = Join-Path $stagingDirectory "Library/bin/FreeCAD.exe"
$portableCommand = Join-Path $stagingDirectory "Library/bin/FreeCADCmd.exe"

if (-not (Test-Path -LiteralPath $portableExecutable)) {
    throw "Portable staging is missing FreeCAD.exe."
}

if (-not (Test-Path -LiteralPath $portableCommand)) {
    throw "Portable staging is missing FreeCADCmd.exe."
}

if (-not $SkipPortableSmokeTest) {
    $previousPath = $env:PATH
    $previousPythonHome = $env:PYTHONHOME

    try {
        $env:PATH = "$(Join-Path $stagingDirectory 'Library/bin');$stagingDirectory;$(Join-Path $stagingDirectory 'Scripts');$previousPath"
        $env:PYTHONHOME = $stagingDirectory

        Write-Host "Running portable FreeCADCmd smoke test..."
        & $portableCommand --version

        if ($LASTEXITCODE -ne 0) {
            throw "Portable FreeCADCmd smoke test failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        $env:PATH = $previousPath
        $env:PYTHONHOME = $previousPythonHome
    }
}

Write-Host "Compressing portable runtime..."
& 7z a -t7z -mx=7 -mmt=on $archivePath (Join-Path $stagingDirectory "*")
if ($LASTEXITCODE -ne 0) {
    throw "7-Zip packaging failed with exit code $LASTEXITCODE."
}

$checksum = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
"$checksum  $([System.IO.Path]::GetFileName($archivePath))" | Set-Content `
    -LiteralPath $checksumPath `
    -Encoding ascii

Write-Host "Portable baseline package created."
Write-Host "Archive: $archivePath"
Write-Host "Checksum: $checksumPath"
