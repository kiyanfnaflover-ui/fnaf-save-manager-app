# -*- mode: python ; coding: utf-8 -*-

import os
import PySide6

# Get Qt plugins path
qt_plugins_path = os.path.join(os.path.dirname(PySide6.__file__), 'plugins')
imageformats_path = os.path.join(qt_plugins_path, 'imageformats')

a = Analysis(
    ['fnaf_save.py'],
    pathex=[],
    binaries=[
        (os.path.join(imageformats_path, 'qgif.dll'), 'imageformats'),
        (os.path.join(imageformats_path, 'qico.dll'), 'imageformats'),
        (os.path.join(imageformats_path, 'qjpeg.dll'), 'imageformats'),
        (os.path.join(imageformats_path, 'qsvg.dll'), 'imageformats'),
    ],
    datas=[('assets', 'assets'), ('favicon.png', '.'), ('favicon.ico', '.')],
    hiddenimports=[
        'PySide6.QtImageFormats',
        'PySide6.QtSvg',
    ],
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
    name='fnaf_save_v3',
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
    icon=['favicon.ico'],
    version=os.path.abspath('version_info.txt'),
)