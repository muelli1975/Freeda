from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH)
icon = root / "assets" / "Freeda.ico"

a = Analysis(
    ["Freeda.py"],
    pathex=[str(root)],
    binaries=[],
    datas=collect_data_files("customtkinter") + [
        (str(root / "assets" / "ready.wav"), "assets"),
        (str(root / "assets" / "Freeda.ico"), "assets"),
    ],
    hiddenimports=["PIL._tkinter_finder"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="Freeda",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    exclude_binaries=True,
    console=False,
    icon=str(icon),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Freeda",
)
