# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Base directory
BASE_DIR = os.path.abspath('.')

# Collect data files: UI static build and database template
datas = [
    (os.path.join(BASE_DIR, 'ui', 'dist'), 'ui/dist'),
    (os.path.join(BASE_DIR, 'assets'), 'assets'),
]

# Hidden imports for WebView2, SQLite, and bioinformatics utils
hiddenimports = [
    'webview',
    'webview.platforms.winforms',
    'clr',
    'pythonnet',
    'bottle',
    'sqlite3',
    'numpy',
    'pandas',
    'openpyxl',
    'reportlab',
    'requests',
    'urllib3',
    'utils.database',
    'utils.bio_alignment',
    'utils.bio_math',
    'tools.dna_generate',
    'tools.primer_designer',
    'tools.qpcr',
    'tools.simulation',
    'api_bridge',
]

a = Analysis(
    [os.path.join(BASE_DIR, 'src', 'main_webview.py')],
    pathex=[os.path.join(BASE_DIR, 'src'), BASE_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'IPython', 'notebook'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DNAx_Lab_Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Windows GUI app (no console popup)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(BASE_DIR, 'assets', 'icon.ico') if os.path.exists(os.path.join(BASE_DIR, 'assets', 'icon.ico')) else None,
)
