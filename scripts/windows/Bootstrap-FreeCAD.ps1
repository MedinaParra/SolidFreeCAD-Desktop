[CmdletBinding()]
param(
    [string]$Repository = "https://github.com/FreeCAD/FreeCAD.git",
    [string]$Tag = "1.1.1",
    [string]$Destination = ".work/FreeCAD",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-Command {
    param([Parameter(Mandatory)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

function Resolve-AbsolutePath {
    param([Parameter(Mandatory)][string]$Path)

    if ([System.IO.Path]::IsPathFullyQualified($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath(
        (Join-Path -Path (Get-Location) -ChildPath $Path)
    )
}

Assert-Command -Name "git"

$resolvedDestination = Resolve-AbsolutePath -Path $Destination

if (Test-Path -LiteralPath $resolvedDestination) {
    if (-not $Force) {
        throw "Destination already exists: $resolvedDestination. Use -Force to replace it."
    }

    Write-Host "Removing existing source directory: $resolvedDestination"
    Remove-Item -LiteralPath $resolvedDestination -Recurse -Force
}

$parent = Split-Path -Parent $resolvedDestination
if ([string]::IsNullOrWhiteSpace($parent)) {
    throw "Unable to resolve the parent directory for: $resolvedDestination"
}

New-Item -ItemType Directory -Path $parent -Force | Out-Null

Write-Host "Cloning FreeCAD tag '$Tag' into '$resolvedDestination'..."
& git clone `
    --depth 1 `
    --branch $Tag `
    --recurse-submodules `
    --shallow-submodules `
    $Repository `
    $resolvedDestination

if ($LASTEXITCODE -ne 0) {
    throw "FreeCAD source clone failed with exit code $LASTEXITCODE."
}

$gitDirectory = Join-Path $resolvedDestination ".git"
if (-not (Test-Path -LiteralPath $gitDirectory)) {
    throw "Bootstrap completed without a valid Git checkout at $resolvedDestination."
}

$commit = (& git -C $resolvedDestination rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($commit)) {
    throw "Unable to resolve the checked-out FreeCAD commit."
}

Write-Host "FreeCAD source ready."
Write-Host "Tag: $Tag"
Write-Host "Commit: $commit"
Write-Host "Path: $resolvedDestination"
