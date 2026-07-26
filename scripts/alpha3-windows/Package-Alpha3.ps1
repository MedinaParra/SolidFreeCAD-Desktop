[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$RuntimeRoot,

    [string]$OutputDirectory = "dist",

    [string]$ProductVersion = "0.1.0-alpha.3",

    [string]$FreeCADTag = "1.1.1",

    [Parameter(Mandatory)]
    [string]$FreeCADCommit,

    [Parameter(Mandatory)]
    [string]$SolidFreeCADCommit,

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
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )

    & robocopy $Source $Destination /E /R:2 /W:2 /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -gt 7) {
        throw "Robocopy failed with exit code $LASTEXITCODE."
    }
}

function Find-InnoCompiler {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    throw "Inno Setup compiler ISCC.exe was not found."
}

function Find-CSharpCompiler {
    $candidates = @(
        (Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"),
        (Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    $command = Get-Command csc.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    throw "C# compiler csc.exe was not found."
}

$resolvedOutputForDiagnostics = Resolve-AbsolutePath -Path $OutputDirectory
trap {
    New-Item -ItemType Directory -Path $resolvedOutputForDiagnostics -Force | Out-Null
    $diagnosticPath = Join-Path $resolvedOutputForDiagnostics "alpha3-packaging-error.txt"
    $details = $_ | Format-List * -Force | Out-String
    @"
SolidFreeCAD alpha.3 packaging failure
Stage: $script:CurrentStage
UTC: $([DateTime]::UtcNow.ToString("o"))

$details
"@ | Set-Content -LiteralPath $diagnosticPath -Encoding utf8
    Write-Error "Alpha.3 packaging failed during '$script:CurrentStage'. Diagnostic: $diagnosticPath"
    exit 1
}

foreach ($command in @("robocopy", "7z")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required command '$command' was not found in PATH."
    }
}

$resolvedRuntime = Resolve-AbsolutePath -Path $RuntimeRoot
$resolvedOutput = $resolvedOutputForDiagnostics
$freeCADExecutable = Join-Path $resolvedRuntime "Library/bin/FreeCAD.exe"
$freeCADCommand = Join-Path $resolvedRuntime "Library/bin/FreeCADCmd.exe"
$workbenchPath = Join-Path $resolvedRuntime "Library/Mod/SolidFreeCAD/InitGui.py"

foreach ($required in @($freeCADExecutable, $freeCADCommand, $workbenchPath)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Alpha.3 runtime is incomplete: $required"
    }
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

foreach ($path in @(
    $stagingDirectory,
    $archivePath,
    $archiveChecksumPath,
    $installerPath,
    $installerChecksumPath,
    $issPath,
    $launcherSourcePath,
    (Join-Path $resolvedOutput "alpha3-packaging-error.txt")
)) {
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}

$script:CurrentStage = "copy runtime"
Write-Host "Creating SolidFreeCAD alpha.3 staging directory..."
Invoke-Robocopy -Source $resolvedRuntime -Destination $stagingDirectory

Get-ChildItem -LiteralPath $stagingDirectory -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -like "*BASELINE*" -or
        $_.Name -eq "Start-SolidFreeCAD.cmd" -or
        $_.Name -eq "README-SOLIDFREECAD.txt" -or
        $_.Name -eq "BUILD-METADATA.json"
    } |
    Remove-Item -Force

$script:CurrentStage = "portable configuration"
$userData = Join-Path $stagingDirectory "UserData"
$userImages = Join-Path $userData "Gui/images"
New-Item -ItemType Directory -Path $userImages -Force | Out-Null

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
<FCParameters>
  <FCParamGroup Name="Root"/>
</FCParameters>
'@

Set-Content -LiteralPath (Join-Path $userData "user.cfg") -Value $userConfig -Encoding utf8
Set-Content -LiteralPath (Join-Path $userData "system.cfg") -Value $systemConfig -Encoding utf8

$script:CurrentStage = "splash generation"
Write-Host "Generating SolidFreeCAD splash image..."
Add-Type -AssemblyName System.Drawing
$width = 1024
$height = 576
$bitmap = [System.Drawing.Bitmap]::new($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$rectangle = [System.Drawing.Rectangle]::new(0, 0, $width, $height)
$background = [System.Drawing.Drawing2D.LinearGradientBrush]::new(
    $rectangle,
    [System.Drawing.Color]::FromArgb(16, 31, 50),
    [System.Drawing.Color]::FromArgb(36, 94, 160),
    25.0
)
$accent = [System.Drawing.SolidBrush]::new(
    [System.Drawing.Color]::FromArgb(70, 155, 255)
)
$hole = [System.Drawing.SolidBrush]::new(
    [System.Drawing.Color]::FromArgb(23, 50, 88)
)
$white = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)
$muted = [System.Drawing.SolidBrush]::new(
    [System.Drawing.Color]::FromArgb(205, 222, 240)
)
$titleFont = [System.Drawing.Font]::new(
    "Segoe UI",
    54,
    [System.Drawing.FontStyle]::Bold
)
$subtitleFont = [System.Drawing.Font]::new(
    "Segoe UI",
    21,
    [System.Drawing.FontStyle]::Regular
)
$smallFont = [System.Drawing.Font]::new(
    "Segoe UI",
    13,
    [System.Drawing.FontStyle]::Regular
)

try {
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.FillRectangle($background, $rectangle)
    $graphics.FillEllipse($accent, 72, 156, 150, 150)
    $graphics.FillEllipse($hole, 112, 196, 70, 70)
    $graphics.FillRectangle($accent, 36, 211, 222, 40)
    $graphics.FillRectangle($accent, 127, 120, 40, 222)
    $graphics.DrawString("SolidFreeCAD", $titleFont, $white, 300, 175)
    $graphics.DrawString(
        "Diseño mecánico paramétrico para Windows",
        $subtitleFont,
        $muted,
        304,
        252
    )
    $graphics.DrawString(
        "Motor FreeCAD $FreeCADTag · SolidFreeCAD $ProductVersion",
        $smallFont,
        $muted,
        306,
        315
    )
    $graphics.DrawString(
        "Portable · local · sin servicios externos",
        $smallFont,
        $muted,
        306,
        348
    )

    $splashPath = Join-Path $userImages "splash_image.png"
    $bitmap.Save($splashPath, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $graphics.Dispose()
    $bitmap.Dispose()
    $background.Dispose()
    $accent.Dispose()
    $hole.Dispose()
    $white.Dispose()
    $muted.Dispose()
    $titleFont.Dispose()
    $subtitleFont.Dispose()
    $smallFont.Dispose()
}

$script:CurrentStage = "launcher compilation"
Write-Host "Compiling graphical SolidFreeCAD launcher..."
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
        string executable = Path.Combine(root, "Library", "bin", "FreeCAD.exe");
        string userData = Path.Combine(root, "UserData");
        string userConfig = Path.Combine(userData, "user.cfg");
        string systemConfig = Path.Combine(userData, "system.cfg");

        if (!File.Exists(executable))
        {
            return 2;
        }

        Directory.CreateDirectory(userData);
        StringBuilder arguments = new StringBuilder();
        arguments.Append("--user-cfg ").Append(Quote(userConfig));
        arguments.Append(" --system-cfg ").Append(Quote(systemConfig));
        foreach (string argument in args)
        {
            arguments.Append(" ").Append(Quote(argument));
        }

        ProcessStartInfo info = new ProcessStartInfo();
        info.FileName = executable;
        info.Arguments = arguments.ToString();
        info.WorkingDirectory = root;
        info.UseShellExecute = false;
        info.CreateNoWindow = true;

        string currentPath = Environment.GetEnvironmentVariable("PATH") ?? String.Empty;
        info.EnvironmentVariables["PATH"] =
            Path.Combine(root, "Library", "bin") + ";" +
            root + ";" +
            Path.Combine(root, "Scripts") + ";" + currentPath;
        info.EnvironmentVariables["PYTHONHOME"] = root;
        info.EnvironmentVariables["FREECAD_USER_HOME"] = userData;
        info.EnvironmentVariables["FREECAD_USER_DATA"] = userData;

        Process process = Process.Start(info);
        return process == null ? 3 : 0;
    }
}
'@

Set-Content -LiteralPath $launcherSourcePath -Value $launcherSource -Encoding utf8
$launcherPath = Join-Path $stagingDirectory "SolidFreeCADLauncher.exe"
$csharpCompiler = Find-CSharpCompiler
& $csharpCompiler `
    /nologo `
    /target:winexe `
    /optimize+ `
    "/out:$launcherPath" `
    $launcherSourcePath
if ($LASTEXITCODE -ne 0) {
    throw "SolidFreeCAD launcher compilation failed with exit code $LASTEXITCODE."
}

if (-not (Test-Path -LiteralPath $launcherPath)) {
    throw "SolidFreeCADLauncher.exe was not generated."
}

$script:CurrentStage = "metadata and example"
$readme = @"
SolidFreeCAD Desktop - Windows alpha.3
======================================

SolidFreeCAD version: $ProductVersion
FreeCAD engine: $FreeCADTag
Platform: Windows x64

Launch:
  SolidFreeCADLauncher.exe

Main additions in alpha.3:
- SolidFreeCAD opens as the default workbench.
- Portable user configuration isolated from other FreeCAD installations.
- SolidFreeCAD splash and window branding.
- Simplified dockable shaft property panel.
- Parametric stepped shaft with editable keyway.
- Windows installer and portable archive.

The full standard FreeCAD property editor remains available as an advanced
fallback. Ubuntu platform files remain preserved separately in the repository.
"@

Set-Content `
    -LiteralPath (Join-Path $stagingDirectory "README-SOLIDFREECAD.txt") `
    -Value $readme `
    -Encoding utf8

if ($ExampleFile) {
    $resolvedExample = Resolve-AbsolutePath -Path $ExampleFile
    if (-not (Test-Path -LiteralPath $resolvedExample)) {
        throw "Example FCStd file was not found: $resolvedExample"
    }

    $examplesDirectory = Join-Path $stagingDirectory "Examples"
    New-Item -ItemType Directory -Path $examplesDirectory -Force | Out-Null
    Copy-Item `
        -LiteralPath $resolvedExample `
        -Destination (Join-Path $examplesDirectory "Eje-Parametrico-Demo.FCStd") `
        -Force
}

$metadata = [ordered]@{
    product = "SolidFreeCAD Desktop"
    productVersion = $ProductVersion
    packageKind = "windows-alpha3-branded"
    architecture = "x86_64"
    freecadTag = $FreeCADTag
    freecadCommit = $FreeCADCommit
    solidFreeCADCommit = $SolidFreeCADCommit
    createdUtc = [DateTime]::UtcNow.ToString("o")
    brandedLauncher = $true
    isolatedUserConfiguration = $true
    autoWorkbench = "SolidFreeCADWorkbench"
    propertyPanel = "shaft-simplified"
    installer = "Inno Setup"
}

$metadata | ConvertTo-Json -Depth 5 | Set-Content `
    -LiteralPath (Join-Path $stagingDirectory "BUILD-METADATA.json") `
    -Encoding utf8

$script:CurrentStage = "portable compression"
Write-Host "Compressing SolidFreeCAD portable archive..."
& 7z a -t7z -mx=5 -mmt=on $archivePath (Join-Path $stagingDirectory "*")
if ($LASTEXITCODE -ne 0) {
    throw "7-Zip packaging failed with exit code $LASTEXITCODE."
}

$archiveChecksum = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
"$archiveChecksum  $([System.IO.Path]::GetFileName($archivePath))" | Set-Content `
    -LiteralPath $archiveChecksumPath `
    -Encoding ascii

$script:CurrentStage = "installer compilation"
$innoScript = @"
#define ProductVersion "$ProductVersion"
#define SourceRoot "$stagingDirectory"

[Setup]
AppId={{7D1BC0D3-4672-4AA2-91B4-53D7198E7334}
AppName=SolidFreeCAD Desktop
AppVersion={#ProductVersion}
AppPublisher=MedinaParra
AppPublisherURL=https://github.com/MedinaParra/SolidFreeCAD-Desktop
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
SetupLogging=yes

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
Write-Host "Building Windows installer with $innoCompiler..."
& $innoCompiler $issPath
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compilation failed with exit code $LASTEXITCODE."
}

if (-not (Test-Path -LiteralPath $installerPath)) {
    throw "Installer was not generated: $installerPath"
}

$installerChecksum = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
"$installerChecksum  $([System.IO.Path]::GetFileName($installerPath))" | Set-Content `
    -LiteralPath $installerChecksumPath `
    -Encoding ascii

$script:CurrentStage = "complete"
Write-Host "SolidFreeCAD alpha.3 packages created."
Write-Host "Portable: $archivePath"
Write-Host "Installer: $installerPath"
