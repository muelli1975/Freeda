"""Portable ExifTool metadata transfer, following the other stereo tools."""
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from .resources import tool_path


@dataclass(frozen=True)
class MetadataCopyResult:
    success: bool
    message: str = ""


def find_exiftool_path():
    for name in ("exiftool.exe", "exiftool"):
        path = tool_path(name)
        if path.is_file():
            return path
    found = shutil.which("exiftool") or shutil.which("exiftool.exe")
    return Path(found) if found else None


def copy_metadata(source: Path, target: Path, size: tuple[int, int], *, dpi=None):
    source, target = Path(source), Path(target)
    if not source.is_file():
        return MetadataCopyResult(False, "Keine gültige Metadatenquelle.")
    if not target.is_file():
        return MetadataCopyResult(False, "Zieldatei existiert nicht.")
    if source.resolve() == target.resolve():
        return MetadataCopyResult(False, "Originaldatei darf nicht verändert werden.")
    executable = find_exiftool_path()
    if executable is None:
        return MetadataCopyResult(False, "ExifTool nicht gefunden.")
    excluded = ("Preview:all", "ThumbnailImage", "Orientation", "MPF:all",
        "ImageWidth", "ImageHeight", "ImageLength", "ExifImageWidth", "ExifImageHeight",
        "RelatedImageWidth", "RelatedImageHeight", "XResolution", "YResolution",
        "ResolutionUnit", "PixelsPerUnitX", "PixelsPerUnitY", "PixelUnits")
    command = [str(executable), "-overwrite_original", "-TagsFromFile", str(source.resolve()),
        *["--" + tag for tag in excluded],
        f"-ExifImageWidth={size[0]}", f"-ExifImageHeight={size[1]}"]
    if dpi is not None:
        command += [f"-EXIF:XResolution={dpi}", f"-EXIF:YResolution={dpi}", "-EXIF:ResolutionUnit=inches"]
    command.append(str(target.resolve()))
    try:
        # UTF-8 stdin avoids the Windows launcher's lossy command-line conversion.
        # Unix filenames containing a newline need the normal argument interface.
        stdin_arguments = not any("\n" in arg or "\r" in arg for arg in command[1:])
        invocation = [command[0], "-charset", "filename=UTF8", "-@", "-"] if stdin_arguments else command
        completed = subprocess.run(invocation,
            input="\n".join(command[1:]) + "\n" if stdin_arguments else None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", check=False, timeout=120,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as error:
        return MetadataCopyResult(False, str(error))
    if completed.returncode:
        return MetadataCopyResult(False, (completed.stderr or completed.stdout or "ExifTool meldete einen Fehler.").strip())
    return MetadataCopyResult(True)
