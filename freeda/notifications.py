from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def play_ready_sound(path: Path) -> bool:
    path = Path(path)
    if not path.is_file():
        return False
    if sys.platform.startswith("win"):
        try:
            import winsound
            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            return True
        except Exception:
            return False
    player = None
    if sys.platform == "darwin":
        player = shutil.which("afplay")
    elif sys.platform.startswith("linux"):
        for name in ("paplay", "pw-play", "aplay"):
            player = shutil.which(name)
            if player:
                break
    if not player:
        return False
    try:
        subprocess.Popen([player, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False
