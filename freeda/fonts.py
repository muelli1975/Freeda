from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path


def _windows_fonts() -> dict[str, Path]:
    fonts: dict[str, Path] = {}
    if not sys.platform.startswith("win"):
        return fonts
    import winreg
    key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
    font_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    user_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts"
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(hive, key_path) as key:
                for index in range(winreg.QueryInfoKey(key)[1]):
                    name, value, _ = winreg.EnumValue(key, index)
                    family = name.rsplit(" (", 1)[0].strip()
                    path = Path(value)
                    if not path.is_absolute():
                        path = font_dir / value
                        if not path.is_file():
                            path = user_dir / value
                    if path.is_file():
                        fonts.setdefault(family, path)
        except OSError:
            continue
    return fonts


@lru_cache(maxsize=1)
def _font_catalog():
    if sys.platform.startswith("win"):
        return _windows_fonts()
    from PIL import ImageFont
    directories = ([Path("/System/Library/Fonts"), Path("/Library/Fonts"), Path.home()/"Library/Fonts"]
        if sys.platform == "darwin" else [Path("/usr/share/fonts"),Path("/usr/local/share/fonts"),Path.home()/".local/share/fonts",Path.home()/".fonts"])
    fonts = {}
    for directory in directories:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.suffix.lower() not in (".ttf", ".otf", ".ttc"):
                continue
            try:
                family, style = ImageFont.truetype(str(path),12).getname()
                name = family if style.lower() in ("regular","normal","book") else f"{family} {style}"
                fonts.setdefault(name,path)
            except OSError:
                continue
    return fonts


def available_fonts() -> list[str]:
    names = sorted(_font_catalog(), key=str.casefold)
    if "Segoe UI" in names:
        names.remove("Segoe UI")
        names.insert(0, "Segoe UI")
    preferred = "Arial" if sys.platform == "darwin" else "DejaVu Sans"
    if preferred in names and not sys.platform.startswith("win"):
        names.remove(preferred)
        names.insert(0, preferred)
    return names or ["Segoe UI", "Arial", "DejaVu Sans"]


def resolve_font(family: str) -> str | None:
    fonts = _font_catalog()
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
