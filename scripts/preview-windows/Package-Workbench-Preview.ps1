[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$RuntimeRoot,

    [string]$OutputDirectory = "dist",

    [string]$ProductVersion = "0.1.0-alpha.2",

    [string]$FreeCADTag = "1.1.1",

    [Parameter(Mandatory)]
    [string]$FreeCADCommit,

    [Parameter(Mandatory)]
    [string]$SolidFreeCADCommit,

    [string]$ExampleFile
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Resolve-AbsolutePath {
    param([Parameter(Mandatory)][string]$Path)

    if ([System.IO.Path]::IsPathFullyQualified($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
}

function Invoke-Robocopy {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )

    & robocopy $Source $Destination /E /R:2 /W:2 /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -gt 7) {
        throw "Robocopy failed with exit code $LASTEXITCODE."
    }
}

foreach ($command in @("robocopy", "7z")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required command '$command' was not found in PATH."
    }
}

$resolvedRuntime = Resolve-AbsolutePath -Path $RuntimeRoot
$resolvedOutput = Resolve-AbsolutePath -Path $OutputDirectory
$freeCADExecutable = Join-Path $resolvedRuntime "Library/bin/FreeCAD.exe"
$freeCADCommand = Join-Path $resolvedRuntime "Library/bin/FreeCADCmd.exe"
$workbenchPath = Join-Path $resolvedRuntime "Library/Mod/SolidFreeCAD/InitGui.py"

foreach ($required in @($freeCADExecutable, $freeCADCommand, $workbenchPath)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Preview runtime is incomplete: $required"
    }
}

New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null

$packageName = "SolidFreeCAD-$ProductVersion-FreeCAD-$FreeCADTag-Windows-x64-Portable-Preview"
$stagingDirectory = Join-Path $resolvedOutput $packageName
$archivePath = Join-Path $resolvedOutput "$packageName.7z"
$checksumPath = "$archivePath.sha256"

foreach ($path in @($stagingDirectory, $archivePath, $checksumPath)) {
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}

Write-Host "Copying preview runtime..."
Invoke-Robocopy -Source $resolvedRuntime -Destination $stagingDirectory

Get-ChildItem -LiteralPath $stagingDirectory -Filter "*BASELINE*" -File -ErrorAction SilentlyContinue |
    Remove-Item -Force

$launcher = @'
@echo off
setlocal
set "ROOT=%~dp0"
set "PATH=%ROOT%Library\bin;%ROOT%;%ROOT%Scripts;%PATH%"
set "PYTHONHOME=%ROOT%"
start "SolidFreeCAD Desktop" "%ROOT%Library\bin\FreeCAD.exe" %*
endlocal
'@

Set-Content `
    -LiteralPath (Join-Path $stagingDirectory "Start-SolidFreeCAD.cmd") `
    -Value $launcher `
    -Encoding ascii

$readme = @"
SolidFreeCAD Desktop - Windows workbench preview
================================================

SolidFreeCAD version: $ProductVersion
FreeCAD engine tag: $FreeCADTag
Platform: Windows x64

This preview contains the official FreeCAD engine plus the first shared
SolidFreeCAD workbench overlay.

Available in this iteration:
- SolidFreeCAD workbench.
- Native New, Open, Save, Undo and Redo commands.
- Part Design and Sketcher shortcuts.
- Parametric stepped-shaft generator.
- Editable shaft lengths, diameters and keyway properties.
- Standard orthographic and axonometric views.

Launch:
  Start-SolidFreeCAD.cmd

After opening, select SolidFreeCAD in the workbench selector if it is not
already active. The next branding iteration will make the shell the default
without requiring manual selection.

The Ubuntu track remains preserved in the repository and will reuse the same
platform-neutral workbench overlay in a future build.
"@

Set-Content `
    -LiteralPath (Join-Path $stagingDirectory "README-SOLIDFREECAD.txt") `
    -Value $readme `
    -Encoding utf8

$metadata = [ordered]@{
    product = "SolidFreeCAD Desktop"
    productVersion = $ProductVersion
    packageKind = "windows-portable-workbench-preview"
    architecture = "x86_64"
    freecadTag = $FreeCADTag
    freecadCommit = $FreeCADCommit
    solidFreeCADCommit = $SolidFreeCADCommit
    createdUtc = [DateTime]::UtcNow.ToString("o")
    brandedExecutable = $false
    workbenchOverlay = $true
    includedFeatures = @(
        "SolidFreeCAD workbench",
        "parametric stepped shaft",
        "editable keyway",
        "Part Design shortcuts",
        "Sketcher shortcuts"
    )
}

$metadata | ConvertTo-Json -Depth 5 | Set-Content `
    -LiteralPath (Join-Path $stagingDirectory "BUILD-METADATA.json") `
    -Encoding utf8

if ($ExampleFile) {
    $resolvedExample = Resolve-AbsolutePath -Path $ExampleFile
    if (-not (Test-Path -LiteralPath $resolvedExample)) {
        throw "Example FCStd file was not found: $resolvedExample"
    }

    $examplesDirectory = Join-Path $stagingDirectory "Examples"
    New-Item -ItemType Directory -Path $examplesDirectory -Force | Out-Null
    Copy-Item -LiteralPath $resolvedExample `
        -Destination (Join-Path $examplesDirectory "Eje-Parametrico-Demo.FCStd") `
        -Force
}

Write-Host "Compressing SolidFreeCAD workbench preview..."
& 7z a -t7z -mx=7 -mmt=on $archivePath (Join-Path $stagingDirectory "*")
if ($LASTEXITCODE -ne 0) {
    throw "7-Zip packaging failed with exit code $LASTEXITCODE."
}

$checksum = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
"$checksum  $([System.IO.Path]::GetFileName($archivePath))" | Set-Content `
    -LiteralPath $checksumPath `
    -Encoding ascii

Write-Host "SolidFreeCAD workbench preview package created."
Write-Host "Archive: $archivePath"
Write-Host "Checksum: $checksumPath"
