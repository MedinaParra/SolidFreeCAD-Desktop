[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RuntimeRoot,
    [Parameter(Mandatory)][string]$IconPackRoot,
    [string]$OutputDirectory = "dist",
    [string]$ProductVersion = "0.1.0-alpha.4",
    [string]$FreeCADTag = "1.1.1",
    [Parameter(Mandatory)][string]$FreeCADCommit,
    [Parameter(Mandatory)][string]$SolidFreeCADCommit,
    [string]$ExampleFile
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

function Invoke-Robocopy {
    param([Parameter(Mandatory)][string]$Source,[Parameter(Mandatory)][string]$Destination)
    & robocopy $Source $Destination /E /R:2 /W:2 /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -gt 7) { throw "Robocopy failed with exit code $LASTEXITCODE." }
}

function Find-InnoCompiler {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) { return $candidate }
    }
    throw "Inno Setup compiler ISCC.exe was not found."
}

function Find-CSharpCompiler {
    $candidates = @(
        (Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"),
        (Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    $command = Get-Command csc.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    throw "C# compiler csc.exe was not found."
}

$resolvedOutput = Resolve-AbsolutePath -Path $OutputDirectory
trap {
    New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null
    $diagnosticPath = Join-Path $resolvedOutput "alpha4-packaging-error.txt"
    $details = $_ | Format-List * -Force | Out-String
    @"
SolidFreeCAD alpha.4 packaging failure
Stage: $script:CurrentStage
UTC: $([DateTime]::UtcNow.ToString("o"))

$details
"@ | Set-Content -LiteralPath $diagnosticPath -Encoding utf8
    Write-Error "Alpha.4 packaging failed during '$script:CurrentStage'. Diagnostic: $diagnosticPath"
    exit 1
}

foreach ($command in @("robocopy", "7z")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required command '$command' was not found in PATH."
    }
}

$resolvedRuntime = Resolve-AbsolutePath -Path $RuntimeRoot
$resolvedIconPackRoot = Resolve-AbsolutePath -Path $IconPackRoot
$resolvedIcons = Join-Path $resolvedIconPackRoot "icons"
$freeCADExecutable = Join-Path $resolvedRuntime "Library/bin/FreeCAD.exe"
$workbenchPath = Join-Path $resolvedRuntime "Library/Mod/SolidFreeCAD/InitGui.py"
foreach ($required in @($freeCADExecutable, $workbenchPath, $resolvedIconPackRoot, $resolvedIcons)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Alpha.4 input is incomplete: $required" }
}

New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null
$packageName = "SolidFreeCAD-$ProductVersion-FreeCAD-$FreeCADTag-Windows-x64"
$stagingDirectory = Join-Path $resolvedOutput "$packageName-Portable"
$archivePath = "$stagingDirectory.7z"
$archiveChecksumPath = "$archivePath.sha256"
$installerBaseName = "$packageName-Setup"
$installerPath = Join-Path $resolvedOutput "$installerBaseName.exe"
$installerChecksumPath = "$installerPath.sha256"
$issPath = Join-Path $resolvedOutput "$installerBaseName.iss"
$launcherSourcePath = Join-Path $resolvedOutput "SolidFreeCADLauncher.cs"
$iconPackPath = Join-Path $resolvedOutput "SolidFreeCAD-IconPack-v1.zip"

foreach ($path in @($stagingDirectory,$archivePath,$archiveChecksumPath,$installerPath,$installerChecksumPath,$issPath,$launcherSourcePath,$iconPackPath,(Join-Path $resolvedOutput "alpha4-packaging-error.txt"))) {
    if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Recurse -Force }
}

$script:CurrentStage = "copy runtime"
Write-Host "Creating SolidFreeCAD alpha.4 staging directory..."
Invoke-Robocopy -Source $resolvedRuntime -Destination $stagingDirectory

$script:CurrentStage = "install icon package"
$installedIconRoot = Join-Path $stagingDirectory "Library/Mod/SolidFreeCAD/Resources/icons"
New-Item -ItemType Directory -Path $installedIconRoot -Force | Out-Null
Copy-Item -Path (Join-Path $resolvedIcons "*") -Destination $installedIconRoot -Recurse -Force
$installedIconCount = (Get-ChildItem -LiteralPath $installedIconRoot -Filter "*.svg" -File -Recurse).Count
if ($installedIconCount -lt 12) { throw "Only $installedIconCount SVG icons were installed." }
Compress-Archive -Path (Join-Path $resolvedIconPackRoot "*") -DestinationPath $iconPackPath -CompressionLevel Optimal

$script:CurrentStage = "normalize Qt platform plugins"
$canonicalPluginRoot = Join-Path $stagingDirectory "Library/plugins"
$canonicalPlatformRoot = Join-Path $canonicalPluginRoot "platforms"
New-Item -ItemType Directory -Path $canonicalPlatformRoot -Force | Out-Null

$qwindows = Get-ChildItem -LiteralPath $stagingDirectory -Filter "qwindows.dll" -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $qwindows) {
    throw "Qt Windows platform plugin qwindows.dll was not found in the packaged runtime."
}

$sourcePlatformRoot = $qwindows.Directory.FullName
$sourcePluginRoot = $qwindows.Directory.Parent.FullName
if ([System.IO.Path]::GetFullPath($sourcePluginRoot) -ne [System.IO.Path]::GetFullPath($canonicalPluginRoot)) {
    if ([System.IO.Path]::GetFileName($sourcePluginRoot) -ieq "plugins") {
        Write-Host "Normalizing complete Qt plugin tree from: $sourcePluginRoot"
        Invoke-Robocopy -Source $sourcePluginRoot -Destination $canonicalPluginRoot
    }
    else {
        Write-Host "Normalizing Qt platform plugin directory from: $sourcePlatformRoot"
        Invoke-Robocopy -Source $sourcePlatformRoot -Destination $canonicalPlatformRoot
    }
}

$canonicalQwindows = Join-Path $canonicalPlatformRoot "qwindows.dll"
if (-not (Test-Path -LiteralPath $canonicalQwindows)) {
    Copy-Item -LiteralPath $qwindows.FullName -Destination $canonicalQwindows -Force
}

$qtConf = @"
[Paths]
Prefix=..
Plugins=plugins
Translations=translations
"@
$qtConfPath = Join-Path $stagingDirectory "Library/bin/qt.conf"
Set-Content -LiteralPath $qtConfPath -Value $qtConf -Encoding ascii

$script:CurrentStage = "portable configuration"
$userData = Join-Path $stagingDirectory "UserData"
New-Item -ItemType Directory -Path $userData -Force | Out-Null
$userConfig = @'
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<FCParameters>
  <FCParamGroup Name="Root">
    <FCParamGroup Name="BaseApp">
      <FCParamGroup Name="Preferences">
        <FCParamGroup Name="General">
          <FCText Name="AutoloadModule" Value="SolidFreeCADWorkbench"/>
          <FCText Name="LastModule" Value="SolidFreeCADWorkbench"/>
          <FCBool Name="ShowSplasher" Value="1"/>
        </FCParamGroup>
      </FCParamGroup>
    </FCParamGroup>
  </FCParamGroup>
</FCParameters>
'@
$systemConfig = @'
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<FCParameters><FCParamGroup Name="Root"/></FCParameters>
'@
Set-Content -LiteralPath (Join-Path $userData "user.cfg") -Value $userConfig -Encoding utf8
Set-Content -LiteralPath (Join-Path $userData "system.cfg") -Value $systemConfig -Encoding utf8

$script:CurrentStage = "launcher compilation"
$launcherSource = @'
using System;
using System.Diagnostics;
using System.IO;
using System.Text;

internal static class SolidFreeCADLauncher
{
    private static string Quote(string value)
    {
        return "\"" + value.Replace("\"", "\\\"") + "\"";
    }

    [STAThread]
    private static int Main(string[] args)
    {
        string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(
            Path.DirectorySeparatorChar,
            Path.AltDirectorySeparatorChar
        );
        string library = Path.Combine(root, "Library");
        string bin = Path.Combine(library, "bin");
        string pluginRoot = Path.Combine(library, "plugins");
        string platformRoot = Path.Combine(pluginRoot, "platforms");
        string executable = Path.Combine(bin, "FreeCAD.exe");
        string userData = Path.Combine(root, "UserData");
        string userConfig = Path.Combine(userData, "user.cfg");
        string systemConfig = Path.Combine(userData, "system.cfg");
        string qwindows = Path.Combine(platformRoot, "qwindows.dll");

        if (!File.Exists(executable)) return 2;
        if (!File.Exists(qwindows)) return 4;

        Directory.CreateDirectory(userData);
        StringBuilder arguments = new StringBuilder();
        arguments.Append("--user-cfg ").Append(Quote(userConfig));
        arguments.Append(" --system-cfg ").Append(Quote(systemConfig));
        foreach (string argument in args) arguments.Append(" ").Append(Quote(argument));

        ProcessStartInfo info = new ProcessStartInfo();
        info.FileName = executable;
        info.Arguments = arguments.ToString();
        info.WorkingDirectory = root;
        info.UseShellExecute = false;
        info.CreateNoWindow = true;

        string currentPath = Environment.GetEnvironmentVariable("PATH") ?? String.Empty;
        info.EnvironmentVariables["PATH"] =
            bin + ";" +
            Path.Combine(library, "usr", "bin") + ";" +
            root + ";" +
            Path.Combine(root, "Scripts") + ";" + currentPath;
        info.EnvironmentVariables["PYTHONHOME"] = root;
        info.EnvironmentVariables["FREECAD_USER_HOME"] = userData;
        info.EnvironmentVariables["FREECAD_USER_DATA"] = userData;
        info.EnvironmentVariables["QT_PLUGIN_PATH"] = pluginRoot;
        info.EnvironmentVariables["QT_QPA_PLATFORM_PLUGIN_PATH"] = platformRoot;
        info.EnvironmentVariables["QT_QPA_PLATFORM"] = "windows";

        Process process = Process.Start(info);
        return process == null ? 3 : 0;
    }
}
'@
Set-Content -LiteralPath $launcherSourcePath -Value $launcherSource -Encoding utf8
$launcherPath = Join-Path $stagingDirectory "SolidFreeCADLauncher.exe"
$csharpCompiler = Find-CSharpCompiler
& $csharpCompiler /nologo /target:winexe /optimize+ "/out:$launcherPath" $launcherSourcePath
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $launcherPath)) {
    throw "SolidFreeCAD launcher compilation failed with exit code $LASTEXITCODE."
}

$diagnosticLauncher = @"
@echo off
setlocal
set "ROOT=%~dp0"
set "PATH=%ROOT%Library\bin;%ROOT%Library\usr\bin;%ROOT%;%ROOT%Scripts;%PATH%"
set "PYTHONHOME=%ROOT%"
set "FREECAD_USER_HOME=%ROOT%UserData"
set "FREECAD_USER_DATA=%ROOT%UserData"
set "QT_PLUGIN_PATH=%ROOT%Library\plugins"
set "QT_QPA_PLATFORM_PLUGIN_PATH=%ROOT%Library\plugins\platforms"
set "QT_QPA_PLATFORM=windows"
set "QT_DEBUG_PLUGINS=1"
"%ROOT%Library\bin\FreeCAD.exe" --user-cfg "%ROOT%UserData\user.cfg" --system-cfg "%ROOT%UserData\system.cfg" > "%ROOT%qt-plugin-diagnostic.log" 2>&1
endlocal
"@
Set-Content -LiteralPath (Join-Path $stagingDirectory "Start-SolidFreeCAD-Diagnostic.cmd") -Value $diagnosticLauncher -Encoding ascii

$script:CurrentStage = "metadata and examples"
if ($ExampleFile) {
    $resolvedExample = Resolve-AbsolutePath -Path $ExampleFile
    if (Test-Path -LiteralPath $resolvedExample) {
        $examplesDirectory = Join-Path $stagingDirectory "Examples"
        New-Item -ItemType Directory -Path $examplesDirectory -Force | Out-Null
        Copy-Item -LiteralPath $resolvedExample -Destination (Join-Path $examplesDirectory "Eje-Parametrico-Demo.FCStd") -Force
    }
}

$metadata = [ordered]@{
    product = "SolidFreeCAD Desktop"
    productVersion = $ProductVersion
    packageKind = "windows-alpha4-icons-qt-fix"
    architecture = "x86_64"
    freecadTag = $FreeCADTag
    freecadCommit = $FreeCADCommit
    solidFreeCADCommit = $SolidFreeCADCommit
    createdUtc = [DateTime]::UtcNow.ToString("o")
    qtPluginRoot = "Library/plugins"
    qtPlatformPlugin = "Library/plugins/platforms/qwindows.dll"
    qtConf = "Library/bin/qt.conf"
    iconSystem = "SFC Mechanical Icon System v1"
    iconCount = $installedIconCount
}
$metadata | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $stagingDirectory "BUILD-METADATA.json") -Encoding utf8

$readme = @"
SolidFreeCAD Desktop - Windows alpha.4
======================================

Run: SolidFreeCADLauncher.exe

Qt startup repair:
- qwindows.dll is normalized under Library\plugins\platforms.
- Library\bin\qt.conf points Qt to the packaged plugin directory.
- The launcher sets QT_PLUGIN_PATH and QT_QPA_PLATFORM_PLUGIN_PATH.
- Start-SolidFreeCAD-Diagnostic.cmd creates qt-plugin-diagnostic.log if needed.

This build also includes the original SFC Mechanical Icon System v1.
Ubuntu platform work remains preserved separately in the repository.
"@
Set-Content -LiteralPath (Join-Path $stagingDirectory "README-SOLIDFREECAD.txt") -Value $readme -Encoding utf8

$script:CurrentStage = "portable compression"
& 7z a -t7z -mx=5 -mmt=on $archivePath (Join-Path $stagingDirectory "*")
if ($LASTEXITCODE -ne 0) { throw "7-Zip packaging failed with exit code $LASTEXITCODE." }
$archiveChecksum = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
"$archiveChecksum  $([System.IO.Path]::GetFileName($archivePath))" | Set-Content -LiteralPath $archiveChecksumPath -Encoding ascii

$script:CurrentStage = "installer compilation"
$innoScript = @"
#define ProductVersion "$ProductVersion"
#define SourceRoot "$stagingDirectory"

[Setup]
AppId={{7D1BC0D3-4672-4AA2-91B4-53D7198E7334}
AppName=SolidFreeCAD Desktop
AppVersion={#ProductVersion}
AppPublisher=MedinaParra
DefaultDirName={autopf}\SolidFreeCAD
DefaultGroupName=SolidFreeCAD
OutputDir=$resolvedOutput
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
Write-Host "SolidFreeCAD alpha.4 packages created."
Write-Host "Portable: $archivePath"
Write-Host "Installer: $installerPath"
Write-Host "Icons: $iconPackPath"
