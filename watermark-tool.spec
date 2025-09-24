# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

a = Analysis(
    ['watermark_app\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

ESSENTIAL_QT_PLUGINS = {
    ("platforms", "qwindows.dll"),
    ("styles", "qwindowsvistastyle.dll"),
    ("imageformats", "qico.dll"),
    ("imageformats", "qjpeg.dll"),
    ("imageformats", "qpng.dll"),
    ("imageformats", "qtiff.dll"),
    ("imageformats", "qgif.dll"),
    ("imageformats", "qwbmp.dll"),
}

filtered_datas = []
for src, dest, typecode in a.datas:
    parts = Path(dest).parts
    if len(parts) >= 5 and parts[0] == 'PySide6' and parts[1] == 'Qt' and parts[2] == 'plugins':
        plugin_folder = parts[3]
        filename = parts[-1]
        if (plugin_folder, filename) in ESSENTIAL_QT_PLUGINS:
            filtered_datas.append((src, dest, typecode))
        continue
    filtered_datas.append((src, dest, typecode))

a.datas = filtered_datas

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='watermark-tool',
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
)
