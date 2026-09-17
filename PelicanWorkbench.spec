# -*- mode: python ; coding: utf-8 -*-
"""Reliable Windows one-file build for Pelican Workbench.

PyInstaller is used here because pywebview's own freezing guide recommends it
for Windows/Linux, and it avoids the current Nuitka 4.2.1/pywebview platform
selection conflict seen in the V3.2.x build chain.
"""
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH)

hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops.auto',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets.auto',
    'webview.platforms.edgechromium',
    'webview.platforms.winforms',
    'webview.platforms.win32',
    'pystray._win32',
    'win32timezone',
    'security.runtime_verify',
    'security.public_key',
]
hiddenimports += collect_submodules('webview')

webview_datas = collect_data_files('webview')

datas = [
    (str(ROOT / 'web'), 'web'),
    (str(ROOT / 'security' / 'release_manifest.json'), 'security'),
    (str(ROOT / 'security' / 'release_manifest.sig'), 'security'),
    (str(ROOT / 'VERSION.txt'), '.'),
] + webview_datas

# pywebview is cross-platform. Only Windows backends are needed here.
excludes = [
    'webview.platforms.android',
    'webview.platforms.cocoa',
    'webview.platforms.gtk',
    'webview.platforms.qt',
    'webview.platforms.qt5',
    'webview.platforms.pyside2',
    'webview.platforms.pyside6',
]

a = Analysis(
    [str(ROOT / 'app.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PelicanWorkbench',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
