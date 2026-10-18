[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RuntimeRoot,
    [string]$OutputDirectory = "dist",
    [string]$ProductVersion = "0.1.0-alpha.12"
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$source = (Resolve-Path .).Path
$runtime = (Resolve-Path $RuntimeRoot).Path
$output = [IO.Path]::GetFullPath((Join-Path $source $OutputDirectory))
$package = Join-Path $output "SolidFreeCAD-$ProductVersion-Windows-x64"
New-Item -ItemType Directory -Path $package -Force | Out-Null
if (-not (Test-Path (Join-Path $runtime "bin/FreeCAD.exe"))) { throw "Official runtime is incomplete." }
Move-Item -LiteralPath $runtime -Destination (Join-Path $package "Runtime")
Copy-Item -LiteralPath (Join-Path $source "standalone") -Destination (Join-Path $package "Application") -Recurse
Get-ChildItem (Join-Path $package "Application") -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
$compiler = Join-Path $env:WINDIR "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
if (-not (Test-Path $compiler)) { throw "C# launcher compiler is unavailable." }
& $compiler /nologo /target:winexe /reference:System.Windows.Forms.dll "/out:$package/SolidFreeCAD.exe" (Join-Path $source "scripts/alpha12-windows/SolidFreeCADLauncher.cs")
if ($LASTEXITCODE -ne 0) { throw "Launcher compilation failed." }
@"
SolidFreeCAD Desktop $ProductVersion

Extraiga la carpeta completa y ejecute SolidFreeCAD.exe.
Esta versión utiliza el motor oficial FreeCAD 1.1.1.
Sus archivos de trabajo se guardan en formato FCStd y pueden exportarse a STEP.

Las funciones implementadas y sus límites se documentan en Application/README.md.
Los avisos y licencias del motor y dependencias se conservan dentro de Runtime.
"@ | Set-Content (Join-Path $package "LEEME.txt") -Encoding utf8
@{
    product = "SolidFreeCAD Desktop"; version = $ProductVersion; sourceCommit = $env:GITHUB_SHA
    freecadVersion = "1.1.1"; interface = "Independent Qt window"; runtimeVerifiedSha256 = $env:FREECAD_RUNTIME_SHA256
} | ConvertTo-Json | Set-Content (Join-Path $package "BUILD-METADATA.json") -Encoding utf8
$archive = "$package-Portable.zip"
& 7z a -tzip -mx=5 $archive "$package/*"
if ($LASTEXITCODE -ne 0) { throw "Portable compression failed." }
$hash = (Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  $([IO.Path]::GetFileName($archive))" | Set-Content "$archive.sha256" -Encoding ascii
$inno = "${env:ProgramFiles(x86)}/Inno Setup 6/ISCC.exe"
if (-not (Test-Path $inno)) { throw "Inno Setup is required for the installer." }
$iss = Join-Path $output "SolidFreeCAD-Standalone.iss"
@"
[Setup]
AppId={{041C54EC-6370-4DC0-99EA-CFFDA94BE12B}
AppName=SolidFreeCAD Desktop
AppVersion=$ProductVersion
AppPublisher=MedinaParra
DefaultDirName={localappdata}\Programs\SolidFreeCAD
DefaultGroupName=SolidFreeCAD
PrivilegesRequired=lowest
OutputDir=$output
OutputBaseFilename=SolidFreeCAD-$ProductVersion-Windows-x64-Setup
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "$package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\SolidFreeCAD"; Filename: "{app}\SolidFreeCAD.exe"
Name: "{autodesktop}\SolidFreeCAD"; Filename: "{app}\SolidFreeCAD.exe"
"@ | Set-Content $iss -Encoding utf8
& $inno $iss
if ($LASTEXITCODE -ne 0) { throw "Installer compilation failed." }
$installer = Join-Path $output "SolidFreeCAD-$ProductVersion-Windows-x64-Setup.exe"
$hash = (Get-FileHash $installer -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  $([IO.Path]::GetFileName($installer))" | Set-Content "$installer.sha256" -Encoding ascii
