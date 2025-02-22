# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_submodules
import os

# Get the directory of the spec file
spec_file_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
main_dir = spec_file_dir  # Assume main.py is in the same directory as the .spec file.

ui_dir = os.path.join(main_dir, "ui")  # Explicitly finds where ui directory is
sys.path.insert(0, main_dir)  # Explicitly adding the directory to the path

hiddenimports = collect_submodules('ui')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BNGSort',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources\\BNGSorter_icon.ico'],
)