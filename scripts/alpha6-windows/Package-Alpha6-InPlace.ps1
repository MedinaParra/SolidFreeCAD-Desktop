[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RuntimeRoot,
    [Parameter(Mandatory)][string]$IconPackRoot,
    [string]$OutputDirectory = "dist",
    [string]$ProductVersion = "0.1.0-alpha.6",
    [string]$FreeCADTag = "1.1.1",
    [Parameter(Mandatory)][string]$FreeCADCommit,
    [Parameter(Mandatory)][string]$SolidFreeCADCommit,
    [string]$ExampleFile,
    [string]$StepFile
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$script:CurrentStage = "initialization"

function Resolve-AbsolutePath {
    param([Parameter(Mandatory)][string]$Path)
    if ([System.IO.Path]::IsPathFullyQualified($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
}

function Find-InnoCompiler {
    foreach ($candidate in @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) { return $candidate }
    }
    throw "Inno Setup compiler ISCC.exe was not found."
}

foreach ($command in @("7z")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required command '$command' was not found in PATH."
    }
}

$resolvedRuntime = Resolve-AbsolutePath $RuntimeRoot
$resolvedOutput = Resolve-AbsolutePath $OutputDirectory
$resolvedIconPack = Resolve-AbsolutePath $IconPackRoot
$resolvedIcons = Join-Path $resolvedIconPack "icons"
New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null

trap {
    New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null
    $diagnostic = Join-Path $resolvedOutput "alpha6-packaging-error.txt"
    $details = $_ | Format-List * -Force | Out-String
    @"
SolidFreeCAD alpha.6 packaging failure
Stage: $script:CurrentStage
UTC: $([DateTime]::UtcNow.ToString("o"))

$details
"@ | Set-Content -LiteralPath $diagnostic -Encoding utf8
    Write-Error "Alpha.6 packaging failed during '$script:CurrentStage'. Diagnostic: $diagnostic"
    exit 1
}

$required = @(
    (Join-Path $resolvedRuntime "Library/bin/FreeCAD.exe"),
    (Join-Path $resolvedRuntime "Library/bin/FreeCADCmd.exe"),
    (Join-Path $resolvedRuntime "Library/Mod/SolidFreeCAD/InitGui.py"),
    (Join-Path $resolvedRuntime "Library/Mod/SolidFreeCAD/MechanicalWorkspace.py"),
    (Join-Path $resolvedRuntime "Library/plugins/platforms/qwindows.dll"),
    (Join-Path $resolvedRuntime "SolidFreeCADLauncher.exe"),
    $resolvedIcons
)
foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Alpha.6 input is incomplete: $path" }
}

$packageName = "SolidFreeCAD-$ProductVersion-FreeCAD-$FreeCADTag-Windows-x64"
$archivePath = Join-Path $resolvedOutput "$packageName-Portable.7z"
$archiveChecksumPath = "$archivePath.sha256"
$installerBaseName = "$packageName-Setup"
$installerPath = Join-Path $resolvedOutput "$installerBaseName.exe"
$installerChecksumPath = "$installerPath.sha256"
$issPath = Join-Path $resolvedOutput "$installerBaseName.iss"
$iconPackPath = Join-Path $resolvedOutput "SolidFreeCAD-IconPack-Classic-v3.zip"
$diagnosticPath = Join-Path $resolvedOutput "alpha6-packaging-error.txt"
foreach ($path in @($archivePath,$archiveChecksumPath,$installerPath,$installerChecksumPath,$issPath,$iconPackPath,$diagnosticPath)) {
    if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Recurse -Force }
}

$script:CurrentStage = "install alpha6 resources"
$installedIconRoot = Join-Path $resolvedRuntime "Library/Mod/SolidFreeCAD/Resources/icons"
New-Item -ItemType Directory -Path $installedIconRoot -Force | Out-Null
Copy-Item -Path (Join-Path $resolvedIcons "*") -Destination $installedIconRoot -Recurse -Force
$installedIconCount = (Get-ChildItem -LiteralPath $installedIconRoot -Filter "*.svg" -File -Recurse).Count
if ($installedIconCount -lt 12) { throw "Only $installedIconCount SVG icons were installed." }
Compress-Archive -Path (Join-Path $resolvedIconPack "*") -DestinationPath $iconPackPath -CompressionLevel Optimal

$script:CurrentStage = "install examples and metadata"
$examplesDirectory = Join-Path $resolvedRuntime "Examples"
New-Item -ItemType Directory -Path $examplesDirectory -Force | Out-Null
if ($ExampleFile) {
    $resolvedExample = Resolve-AbsolutePath $ExampleFile
    if (-not (Test-Path -LiteralPath $resolvedExample)) { throw "FCStd example was not found: $resolvedExample" }
    Copy-Item -LiteralPath $resolvedExample -Destination (Join-Path $examplesDirectory "Pieza-Prueba-Alpha6.FCStd") -Force
}
if ($StepFile) {
    $resolvedStep = Resolve-AbsolutePath $StepFile
    if (-not (Test-Path -LiteralPath $resolvedStep)) { throw "STEP example was not found: $resolvedStep" }
    Copy-Item -LiteralPath $resolvedStep -Destination (Join-Path $examplesDirectory "Pieza-Prueba-Alpha6.step") -Force
}

$metadata = [ordered]@{
    product = "SolidFreeCAD Desktop"
    productVersion = $ProductVersion
    packageKind = "windows-alpha6-integrated-mechanical-workflow"
    architecture = "x86_64"
    freecadTag = $FreeCADTag
    freecadCommit = $FreeCADCommit
    solidFreeCADCommit = $SolidFreeCADCommit
    createdUtc = [DateTime]::UtcNow.ToString("o")
    qtPlatformPlugin = "Library/plugins/platforms/qwindows.dll"
    interface = "CommandManager + FeatureManager + PropertyManager + Heads-Up toolbar"
    iconSystem = "SolidFreeCAD Classic Icon Pack v3"
    iconCount = $installedIconCount
}
$metadata | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $resolvedRuntime "BUILD-METADATA.json") -Encoding utf8

@"
SolidFreeCAD Desktop - Windows alpha.6
======================================

Run: SolidFreeCADLauncher.exe

Validated workflow:
- Create and edit a parametric mechanical part.
- Save and reopen native FCStd.
- Export STEP.
- Use the integrated CommandManager, FeatureManager and PropertyManager.

This package uses the official FreeCAD 1.1.1 engine and original SolidFreeCAD visual resources.
"@ | Set-Content -LiteralPath (Join-Path $resolvedRuntime "README-SOLIDFREECAD.txt") -Encoding utf8

$script:CurrentStage = "portable compression"
& 7z a -t7z -mx=5 -mmt=on $archivePath (Join-Path $resolvedRuntime "*")
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $archivePath)) {
    throw "7-Zip packaging failed with exit code $LASTEXITCODE."
}
$archiveChecksum = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
"$archiveChecksum  $([System.IO.Path]::GetFileName($archivePath))" | Set-Content -LiteralPath $archiveChecksumPath -Encoding ascii

$script:CurrentStage = "installer compilation"
$escapedSource = $resolvedRuntime.Replace('"','""')
$escapedOutput = $resolvedOutput.Replace('"','""')
$innoScript = @"
#define ProductVersion "$ProductVersion"
#define SourceRoot "$escapedSource"

[Setup]
AppId={{7D1BC0D3-4672-4AA2-91B4-53D7198E7334}
AppName=SolidFreeCAD Desktop
AppVersion={#ProductVersion}
AppPublisher=MedinaParra
DefaultDirName={autopf}\SolidFreeCAD
DefaultGroupName=SolidFreeCAD
OutputDir=$escapedOutput
OutputBaseFilename=$installerBaseName
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\SolidFreeCADLauncher.exe

[Files]
Source: "{#SourceRoot}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\SolidFreeCAD Desktop"; Filename: "{app}\SolidFreeCADLauncher.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\SolidFreeCAD Desktop"; Filename: "{app}\SolidFreeCADLauncher.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\SolidFreeCADLauncher.exe"; Description: "Iniciar SolidFreeCAD Desktop"; Flags: nowait postinstall skipifsilent
"@
Set-Content -LiteralPath $issPath -Value $innoScript -Encoding utf8
$innoCompiler = Find-InnoCompiler
& $innoCompiler $issPath
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $installerPath)) {
    throw "Inno Setup compilation failed with exit code $LASTEXITCODE."
}
$installerChecksum = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
"$installerChecksum  $([System.IO.Path]::GetFileName($installerPath))" | Set-Content -LiteralPath $installerChecksumPath -Encoding ascii

$script:CurrentStage = "complete"
Write-Host "SolidFreeCAD alpha.6 packages created in place."
Write-Host "Portable: $archivePath"
Write-Host "Installer: $installerPath"
Write-Host "Icons: $iconPackPath"
