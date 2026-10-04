from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / relative


def portable_settings_path() -> Path:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        base = executable.parent
        if sys.platform == "darwin" and executable.parent.name == "MacOS" and executable.parent.parent.name == "Contents":
            base = executable.parents[3]
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "settings.json"
