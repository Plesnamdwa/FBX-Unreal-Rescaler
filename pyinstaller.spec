# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification file for FBX Unreal Rescaler."""

import os
import sys

block_cipher = None

project_dir = os.path.abspath(SPECPATH)
datas = [
    (os.path.join(project_dir, "assets"), "assets"),
]
binaries = []

# Include fbx.pyd, FbxCommon.py, and libfbxsdk.dll if present
for fname in ["fbx.pyd", "fbx.cp310-win_amd64.pyd", "FbxCommon.py", "libfbxsdk.dll"]:
    fpath = os.path.join(project_dir, fname)
    if os.path.exists(fpath):
        if fname.endswith(".dll") or fname.endswith(".pyd"):
            binaries.append((fpath, "."))
        else:
            datas.append((fpath, "."))

icon_file = os.path.join(project_dir, "assets", "icon.ico")
if not os.path.exists(icon_file):
    icon_file = None

a = Analysis(
    [os.path.join(project_dir, "src", "main.py")],
    pathex=[project_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "fbx",
        "FbxCommon",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="FBX_Unreal_Rescaler",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
