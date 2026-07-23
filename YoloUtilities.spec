# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

conda_binary_dir = Path(sys.base_prefix) / "Library" / "bin"
conda_binary_names = (
    "tcl86t.dll",
    "tk86t.dll",
    "libcrypto-3-x64.dll",
    "libssl-3-x64.dll",
    "liblzma.dll",
    "libbz2.dll",
)
conda_binaries = [
    (str(conda_binary_dir / name), ".")
    for name in conda_binary_names
    if (conda_binary_dir / name).is_file()
]

analysis = Analysis(
    ["main.py"],
    pathex=[],
    binaries=conda_binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "cv2",
        "numpy",
        "PIL",
        "imageio",
        "dicttoxml",
        "matplotlib",
        "pandas",
        "scipy",
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="YoloUtilities",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
