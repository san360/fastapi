<#!
.SYNOPSIS
    Packages the existing Microsoft Teams app manifest and icon assets into a zip file.

.DESCRIPTION
    Creates a Teams app package containing:
      - manifest.json (left untouched)
      - color.png
      - outline.png
    All previous logic that mutated the manifest or created backups has been removed per request.

.PARAMETER AppFolder
    Path to the Teams app folder containing manifest.json and icon files.

.PARAMETER OutputZip
    Name (or path) of the output zip file. Defaults to FastAPIBot.zip inside AppFolder.

.PARAMETER DryRun
    If specified, only lists the files that would be packaged.

.EXAMPLE
    ./package-teams-app.ps1

.EXAMPLE
    ./package-teams-app.ps1 -OutputZip MyTeamsApp.zip

.NOTES
    No manifest editing or backup is performed.
#>

param(
    [string]$AppFolder = "teams-app",
    [string]$OutputZip = "FastAPIBot.zip",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'


function Ensure-AppFolder {
    param([string]$Path)
    if (-not (Test-Path $Path)) { throw "App folder '$Path' not found." }
    $required = @('manifest.json','color.png','outline.png')
    foreach ($f in $required) {
        $p = Join-Path $Path $f
        if (-not (Test-Path $p)) { throw "Required file missing: $p" }
    }
}


function Build-Zip {
    param([string]$Folder,[string]$OutputZip)
    $outPath = if ([System.IO.Path]::IsPathRooted($OutputZip)) { $OutputZip } else { Join-Path $Folder $OutputZip }
    # Overwrite existing zip directly (no .bak retention)
    if (Test-Path $outPath) {
        Write-Host "[INFO] Existing package found; overwriting without backup." -ForegroundColor DarkGray
        Remove-Item -LiteralPath $outPath -Force
    }
    $files = @('manifest.json','color.png','outline.png') | ForEach-Object { Join-Path $Folder $_ }
    Compress-Archive -LiteralPath $files -DestinationPath $outPath -Force
    return $outPath
}

Write-Host "[INFO] AppFolder: $AppFolder" -ForegroundColor Cyan
Ensure-AppFolder -Path $AppFolder

if ($DryRun) {
    Write-Host "[DRY-RUN] Files that would be packaged:" -ForegroundColor Yellow
    @('manifest.json','color.png','outline.png') | ForEach-Object { Write-Host "  - $(Join-Path $AppFolder $_)" }
    Write-Host "[DRY-RUN] No changes made." -ForegroundColor Yellow
    exit 0
}

$zipPath = Build-Zip -Folder $AppFolder -OutputZip $OutputZip
Write-Host "[SUCCESS] Teams app package created: $zipPath" -ForegroundColor Green

# Verification summary
$zipInfo = Get-Item $zipPath
Write-Host "[INFO] Package size: $([Math]::Round($zipInfo.Length / 1KB,2)) KB" -ForegroundColor Cyan

# List zip contents quickly (uses .NET) without extracting
Add-Type -AssemblyName System.IO.Compression.FileSystem
$entries = [System.IO.Compression.ZipFile]::OpenRead($zipPath).Entries | Select-Object -ExpandProperty FullName
Write-Host "[INFO] Zip entries:" -ForegroundColor Cyan
$entries | ForEach-Object { Write-Host "  - $_" }

Write-Host "[DONE] Packaging complete (no manifest modifications)." -ForegroundColor Magenta
