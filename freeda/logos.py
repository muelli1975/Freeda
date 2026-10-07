"""Portable logo copies and proportional sizing shared by Web and Print."""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import math
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError
from .models import DEFAULT_LOGO_HEIGHT_PERCENT


@lru_cache(maxsize=8)
def _read_logo(path, modified_ns, file_size):
    with Image.open(path) as source:
        source.load()
        image = ImageOps.exif_transpose(source).convert("RGBA")
    if image.getchannel("A").getextrema()[1] == 0:
        raise ValueError("Die Logodatei enthält keine sichtbaren Pixel.")
    return image


def load_logo(path):
    if path is None:
        raise ValueError("Bitte eine Logodatei wählen.")
    try:
        path = Path(path).resolve()
        info = path.stat()
        return _read_logo(str(path), info.st_mtime_ns, info.st_size)
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
        raise ValueError("Die Logodatei konnte nicht gelesen werden. Bitte eine gültige Bilddatei wählen.") from None


def resolve_logo(base, relative):
    if not relative:
        raise ValueError("Bitte eine Logodatei wählen.")
    base = Path(base).resolve()
    path = (base / relative).resolve()
    if Path(relative).is_absolute() or path.parent != base / "logos":
        raise ValueError("Die gespeicherte Logodatei muss im Ordner logos neben dem Programm liegen.")
    return path


def import_logo(source, base):
    """Keep the original bytes and a relative path; do not alter the source."""
    source = Path(source)
    load_logo(source)
    data = source.read_bytes()
    name = hashlib.sha256(data).hexdigest() + source.suffix.lower()
    folder = Path(base) / "logos"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    if not target.is_file():
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(target)
    return "logos/" + name


@dataclass(frozen=True)
class LogoLayout:
    width: float
    height: float
    gap_top: float
    gap_bottom: float

    @property
    def band_height(self):
        return self.gap_top + self.height + self.gap_bottom


def logo_layout(size, eye_width, height_percent=DEFAULT_LOGO_HEIGHT_PERCENT, *, height=None, gap_top=None, gap_bottom=None):
    """Use the same unit as eye_width; preserve aspect and cap width at 90%."""
    target = height if height is not None else eye_width * height_percent / 100
    if not math.isfinite(target) or target <= 0:
        raise ValueError("Logohöhe: Bitte einen positiven Wert eingeben.")
    ratio = size[0] / size[1]
    target = min(target, eye_width * .9 / ratio)
    top = target * .15 if gap_top is None else gap_top
    bottom = target * .25 if gap_bottom is None else gap_bottom
    if any(not math.isfinite(v) or v < 0 for v in (top,bottom)):
        raise ValueError("Textabstände: Bitte Werte ab 0 mm eingeben.")
    return LogoLayout(target * ratio, target, top, bottom)
