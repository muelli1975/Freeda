from __future__ import annotations

import os
import sys
from pathlib import Path


def _windows_fonts() -> dict[str, Path]:
    fonts: dict[str, Path] = {}
    if not sys.platform.startswith("win"):
        return fonts
    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            count = winreg.QueryInfoKey(key)[1]
            windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
            font_dir = windir / "Fonts"
            for index in range(count):
                name, value, _ = winreg.EnumValue(key, index)
                family = name.rsplit(" (", 1)[0].strip()
                path = Path(value)
                if not path.is_absolute():
                    path = font_dir / path
                if path.is_file():
                    fonts.setdefault(family, path)
    except OSError:
        pass
    return fonts


def available_fonts() -> list[str]:
    names = sorted(_windows_fonts(), key=str.casefold)
    if "Segoe UI" in names:
        names.remove("Segoe UI")
        names.insert(0, "Segoe UI")
    return names or ["Segoe UI", "Arial", "DejaVu Sans"]


def resolve_font(family: str) -> str | None:
    fonts = _windows_fonts()
    if family in fonts:
        return str(fonts[family])
    folded = family.casefold()
    for name, path in fonts.items():
        if name.casefold() == folded:
            return str(path)

    # Pillow/FreeType may resolve common font filenames directly.
    fallback_names = {
        "Segoe UI": "segoeui.ttf",
        "Arial": "arial.ttf",
        "DejaVu Sans": "DejaVuSans.ttf",
    }
    return fallback_names.get(family, family if family.lower().endswith((".ttf", ".otf")) else None)
