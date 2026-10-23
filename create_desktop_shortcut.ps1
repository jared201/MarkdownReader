<#
.SYNOPSIS
    Creates a "Markdown Reader" shortcut on the current user's Desktop.

.DESCRIPTION
    The shortcut launches run_markdown_reader.bat from the project directory,
    which activates the .venv virtual environment and starts main.py.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\create_desktop_shortcut.ps1
#>

[CmdletBinding()]
param(
    [string]$ShortcutName = "Markdown Reader"
)

$ErrorActionPreference = "Stop"

# Project root = folder containing this script.
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Launcher   = Join-Path $ProjectDir "run_markdown_reader.bat"

if (-not (Test-Path $Launcher)) {
    throw "Launcher not found: $Launcher"
}

$DesktopDir   = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopDir ("{0}.lnk" -f $ShortcutName)

# Try to use pythonw.exe from the venv as the icon source (it has a nice Python icon).
$VenvPythonW = Join-Path $ProjectDir ".venv\Scripts\pythonw.exe"
$IconPath    = if (Test-Path $VenvPythonW) { $VenvPythonW } else { $Launcher }

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut     = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath       = $Launcher
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.IconLocation     = $IconPath
$Shortcut.Description      = "Markdown Reader (PyQt6) - launches with .venv activated"
$Shortcut.WindowStyle      = 7  # Minimized (the .bat window closes quickly anyway)
$Shortcut.Save()

Write-Host "Desktop shortcut created: $ShortcutPath"
