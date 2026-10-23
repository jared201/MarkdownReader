# Markdown Reader

A lightweight cross-platform desktop **Markdown reader** built with **PyQt6**. It renders `.md` files as styled HTML in a Chromium-backed web view and can export or print the preview to **PDF** with high visual fidelity.

## Features

- Open `.md` files via **File > Open**, drag-and-drop, or a CLI argument.
- GitHub-style HTML preview with tables, task lists, footnotes, header anchors, and **Pygments** syntax highlighting for fenced code.
- **Light / Dark** themes (View > Theme).
- **Export to PDF** (`Ctrl+Shift+P`) using `QWebEnginePage.printToPdf` with A4 layout and print-optimized CSS (page-break rules).
- **Print** (`Ctrl+P`) via the system print dialog.
- **Live reload** — the preview auto-refreshes when the source file changes on disk (debounced).
- **Recent files** list (last 10) plus persisted theme and window geometry via `QSettings`.

## Requirements

- **Python 3.9+** (3.10 or newer recommended).
- OS: Windows, macOS, or Linux — anywhere `PyQt6` and `PyQt6-WebEngine` wheels are available.
- Runtime dependencies (installed via `requirements.txt`):
  - `PyQt6>=6.6`
  - `PyQt6-WebEngine>=6.6`
  - `markdown-it-py>=3.0`
  - `mdit-py-plugins>=0.4`
  - `Pygments>=2.17`

> **Note:** `PyQt6-WebEngine` bundles Chromium and is a large download (~150 MB). Ensure your environment has network access on first install.

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url> MarkdownReader
cd MarkdownReader
```

### 2. Create a virtual environment (recommended)

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux extras

On some minimal Linux distributions, `QtWebEngine` needs additional system libraries (e.g. `libnss3`, `libxkbcommon-x11-0`, `libxcomposite1`, `libxdamage1`, `libxrandr2`, `libgbm1`, `libasound2`). Install them via your distro's package manager if the app fails to start.

## Running the application

From the project root (with the virtual environment activated):

```bash
python main.py
```

Open a file directly from the command line:

```bash
python main.py path/to/document.md
```

Or launch the app and use **File > Open** (`Ctrl+O`), or drag a `.md` file onto the window.

## Desktop shortcut (Windows)

The repo ships with a launcher and a helper script that create a Desktop shortcut which activates the local virtual environment (`.venv`) and starts the app.

1. Make sure the virtual environment exists and dependencies are installed (see **Setup** above). The launcher expects `.venv\Scripts\pythonw.exe` (or `python.exe`) inside the project directory.
2. From the project root, run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\create_desktop_shortcut.ps1
   ```

   This creates **`Markdown Reader.lnk`** on your Desktop. Double-clicking it runs `run_markdown_reader.bat`, which:
   - `cd`s into the project directory,
   - uses `.venv\Scripts\pythonw.exe` (falling back to `python.exe`) so the venv is active for the process,
   - launches `main.py`.

You can also drag a `.md` file onto the shortcut — the file path is forwarded to `main.py` as a CLI argument.

To remove the shortcut, simply delete `Markdown Reader.lnk` from your Desktop.

## Desktop shortcut (macOS)

On macOS, create a small launcher script that activates the virtual environment and use Finder aliases or symlinks for the Desktop and Dock.

1. Make sure the virtual environment exists and dependencies are installed (see **Setup** above). The launcher expects `.venv/bin/python` inside the project directory.
2. From the project root, create `run_markdown_reader.sh`:

   ```bash
   #!/bin/bash
   cd "$(dirname "$0")"
   source .venv/bin/activate
   python main.py "$@"
   ```

   Then make it executable:

   ```bash
   chmod +x run_markdown_reader.sh
   ```

3. **Create Desktop shortcut:**
   Right-click the script in Finder → **Make Alias** and drag the alias to your Desktop (rename to `Markdown Reader`).
   Alternatively, from Terminal:

   ```bash
   ln -s "$(pwd)/run_markdown_reader.sh" ~/Desktop/Markdown\ Reader
   ```

   Double-click the alias to launch. You may need to grant permission in **System Settings > Privacy & Security** the first time.
   Drag-and-drop a `.md` file onto the alias works the same as on Windows.

4. **Add to Dock / Applications menu:**
   - Create `~/Applications` if it doesn't exist and copy the alias or script there.
   - It will appear in Launchpad. Drag the item from Launchpad (or `~/Applications`) onto the Dock.
   - The app's menu bar integrates with macOS automatically.

To remove the shortcut, delete the alias or `run_markdown_reader.sh`.

## Packaging & Releases

This section explains how to package the PyQt6-based Markdown Reader into standalone executables and create installers for distribution via GitHub or GitLab. Packaging uses **PyInstaller**. The resulting bundles are self-contained but large (~150–300 MB) due to bundled Chromium from `PyQt6-WebEngine`.

### Prerequisites
- Clean virtual environment with dependencies from `requirements.txt`.
- Install PyInstaller:
  ```bash
  pip install pyinstaller pyinstaller-hooks-contrib --upgrade
  ```
- Build **on the target OS** (PyInstaller does not reliably cross-compile GUI apps).
- Platform tools: Inno Setup / WiX (Windows), `hdiutil` + Xcode tools (macOS).

### Step 1: Create PyInstaller Spec File
Create `markdown_reader.spec` in the project root:

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

assets_data = collect_data_files('markdown_reader.assets', include_py_files=False)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=assets_data,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MarkdownReader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='path/to/icon.ico' if sys.platform == 'win32' else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MarkdownReader',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Markdown Reader.app',
        icon='path/to/icon.icns',
        bundle_identifier='com.example.markdownreader',
        version='1.0.0',
    )
```

Generate initial spec with:
```bash
pyinstaller --name MarkdownReader --windowed main.py
```
Then edit the `.spec` file. Use `;` (Windows) or `:` (macOS/Linux) as path separator in `--add-data`.

### Step 2: Build per Platform & Create Installers

**Windows**
```powershell
pyinstaller markdown_reader.spec
```
Output: `dist/MarkdownReader/` (folder with `.exe`).

Create installer with **Inno Setup** (example `.iss`):
```iss
[Setup]
AppName=Markdown Reader
AppVersion=1.0.0
DefaultDirName={pf}\Markdown Reader
OutputDir=.
OutputBaseFilename=MarkdownReader-Windows-Setup
[Files]
Source: "dist\MarkdownReader\*"; DestDir: "{app}"; Flags: recursesubdirs
[Icons]
Name: "{autodesktop}\Markdown Reader"; Filename: "{app}\MarkdownReader.exe"
```
Compile with Inno Setup to produce `MarkdownReader-Windows-Setup.exe`.

**macOS**
```bash
pyinstaller markdown_reader.spec
```
Create DMG:
```bash
hdiutil create -volname "Markdown Reader" -srcfolder "./dist/Markdown Reader.app" -ov -format UDZO "MarkdownReader-macOS.dmg"
```
For distribution outside App Store: sign and notarize the `.app` using `codesign` and `xcrun notarytool`.

**Linux** (optional)
```bash
pyinstaller markdown_reader.spec
```
Optionally create AppImage or `.deb`.

Test the packaged app on a clean machine (drag-and-drop, PDF export, no console window).

### Step 3: Releasing

**GitHub (manual)**
- Tag: `git tag v1.0.0 && git push --tags`
- Go to Releases → Draft a new release
- Attach platform artifacts (`.exe` installer, `.dmg`, etc.) and publish.

**GitHub Actions (recommended)**
Create `.github/workflows/build.yml` (matrix build on `windows-latest`, `macos-latest`, `ubuntu-latest`, upload artifacts on tag push).

**GitLab**
Use Releases UI or `.gitlab-ci.yml` with parallel matrix; attach artifacts via Release API.

### Best Practices
- Use semantic versioning (`v1.0.0`).
- Code signing (Authenticode for Windows, Developer ID + notarization for macOS) is strongly recommended.
- Document large download size due to WebEngine.
- Test on clean machines.
- Consider auto-update libraries for future releases.

## Keyboard shortcuts

| Action                | Shortcut         |
|-----------------------|------------------|
| Open file             | `Ctrl+O`         |
| Export as PDF         | `Ctrl+Shift+P`   |
| Print                 | `Ctrl+P`         |
| Quit                  | `Ctrl+Q`         |

Theme selection and recent files are available from the menu bar.

## Project layout

```
MarkdownReader/
├── main.py                       # thin entrypoint
├── requirements.txt
└── markdown_reader/
    ├── app.py                    # QApplication bootstrap
    ├── core/
    │   ├── renderer.py           # Markdown -> HTML (markdown-it-py + Pygments)
    │   ├── pdf_exporter.py       # printToPdf wrapper
    │   ├── file_watcher.py       # debounced QFileSystemWatcher
    │   └── settings.py           # QSettings-backed store
    ├── ui/
    │   └── main_window.py        # MainWindow + menus + QWebEngineView
    └── assets/
        ├── screen-light.css
        ├── screen-dark.css
        └── print.css
```

## Troubleshooting

- **`ModuleNotFoundError: No module named 'PyQt6'`** — activate your virtual environment and re-run `pip install -r requirements.txt`.
- **Blank window / WebEngine fails to initialize on Linux** — install the missing system libraries listed above.
- **PDF export produces an empty file** — ensure the document has finished loading before exporting; the exporter uses the async `pdfPrintingFinished` signal and reports errors in the status bar.
- **Images don't appear** — relative paths are resolved against the source file's directory; make sure the referenced images exist at those relative locations.

## License

Add your preferred license here (e.g. MIT).
