"""Bundle an allowlisted source snapshot and installed runtime license material."""
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys


def prepare(root, package, allowed):
    tracked = subprocess.check_output(["git", "ls-files"], cwd=root, text=True).splitlines()
    destination = package / "source"
    if destination.exists():
        shutil.rmtree(destination)
    for name in tracked:
        relative = Path(name)
        if relative.parts[0] in allowed:
            source = root / relative
            if source.is_file():
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    for name in ("numpy", "Pillow", "customtkinter", "darkdetect", "packaging", "pyinstaller"):
        dist = metadata.distribution(name)
        for relative in dist.files or ():
            if any(part.lower().startswith(("license", "copying", "notice", "copyright")) for part in relative.parts):
                source = Path(dist.locate_file(relative))
                if source.is_file():
                    target = package / "licenses" / name / Path(*[part for part in relative.parts if part not in ("..", ".")])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
