# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import copy_metadata

datas = [('assets\\skaterush_logo.ico', 'assets')]
hiddenimports = ['pkg_resources.extern.jaraco', 'pkg_resources.extern.packaging', 'pkg_resources.extern.appdirs', 'pkg_resources.extern.more_itertools']
datas += copy_metadata('setuptools')
hiddenimports += collect_submodules('jaraco')
hiddenimports += collect_submodules('pkg_resources.extern')


a = Analysis(
    ['skate_game.py'],
    pathex=[],
    binaries=[],
    datas=datas,
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
    name='skate4_fix',
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
    icon=['assets\\skaterush_logo.ico'],
)
