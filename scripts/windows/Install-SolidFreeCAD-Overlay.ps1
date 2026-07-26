[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$SourceDirectory,

    [string]$OverlayDirectory = "overlay",

    [switch]$Force
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

$resolvedSource = Resolve-AbsolutePath -Path $SourceDirectory
$resolvedOverlay = Resolve-AbsolutePath -Path $OverlayDirectory
$environmentRoot = Join-Path $resolvedSource ".pixi/envs/default"
$moduleSource = Join-Path $resolvedOverlay "Mod/SolidFreeCAD"
$moduleDestination = Join-Path $environmentRoot "Library/Mod/SolidFreeCAD"

if (-not (Test-Path -LiteralPath (Join-Path $environmentRoot "Library/bin/FreeCADCmd.exe"))) {
    throw "FreeCAD runtime was not found. Build it before installing the overlay: $environmentRoot"
}

$requiredFiles = @(
    "Init.py",
    "InitGui.py",
    "Commands.py",
    "ShaftFeature.py"
)

foreach ($file in $requiredFiles) {
    $path = Join-Path $moduleSource $file
    if (-not (Test-Path -LiteralPath $path)) {
        throw "SolidFreeCAD overlay file is missing: $path"
    }
}

if (Test-Path -LiteralPath $moduleDestination) {
    if (-not $Force) {
        throw "SolidFreeCAD overlay already exists: $moduleDestination. Use -Force to replace it."
    }

    Remove-Item -LiteralPath $moduleDestination -Recurse -Force
}

New-Item -ItemType Directory -Path $moduleDestination -Force | Out-Null
Copy-Item -Path (Join-Path $moduleSource "*") -Destination $moduleDestination -Recurse -Force

$installedFiles = Get-ChildItem -LiteralPath $moduleDestination -File | Select-Object -ExpandProperty Name
foreach ($file in $requiredFiles) {
    if ($installedFiles -notcontains $file) {
        throw "Overlay installation verification failed for: $file"
    }
}

Write-Host "SolidFreeCAD overlay installed successfully."
Write-Host "Source: $moduleSource"
Write-Host "Destination: $moduleDestination"
