# DNAₓ Lab (Python desktop app)

This repository contains the DNAₓ Lab demo — a minimal, production-oriented Python desktop app (Tkinter) with a left side menu and an Uninstall button. It includes scripts and an NSIS installer template so you can build a standalone Windows installer where end users don't need to install Python.

Structure
- src/: application source
- build/: helper build scripts
- installer/: NSIS installer template
- requirements.txt: developer requirements for building

Quick developer build (Windows, PowerShell)

1. Install Python 3.11+ and ensure `pip` is available.
2. Install build tools on the dev machine:

```powershell
python -m pip install -r requirements.txt
# Install NSIS (makensis) separately from https://nsis.sourceforge.io/Download
```

3. Run the build script to create a single-file exe and the NSIS installer (script will expect `makensis` on PATH):

```powershell
.\build\build_exe.ps1
```

Notes
- The app attempts to run `uninstall.exe` from the installed folder. The NSIS installer template writes an uninstaller binary into the install directory. When users click Uninstall, the app will invoke that uninstaller.
- The build script uses PyInstaller to create a single executable (`--onefile`). You can change to `--onedir` in the script if you prefer an unpacked folder.

Security & signing
- For production, sign your executable and installer with a code-signing certificate.
