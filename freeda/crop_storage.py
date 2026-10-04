"""Optional portable per-folder crop sidecars. Never alter source images."""
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import tempfile
from .models import Crop

FILENAME = "freeda-crops.json"

def _read(directory):
    path = Path(directory) / FILENAME
    if not path.exists():
        return {"version": 1, "images": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("images"), dict):
            raise ValueError
        return data
    except (ValueError, UnicodeError):
        raise ValueError(f"Ungültige Ausschnittdatei: {path}") from None

def load_crops(directory):
    result = {}
    for name, modes in _read(directory)["images"].items():
        if not isinstance(name, str) or Path(name).name != name or not isinstance(modes, dict):
            continue
        valid = {}
        for mode in ("Web", "Print"):
            record = modes.get(mode)
            if not isinstance(record, dict):
                continue
            try:
                values = [record[field] for field in ("x", "y", "width", "height")]
                if any(isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) for v in values):
                    continue
                crop = Crop(*values)
                if crop.width <= 0 or crop.height <= 0 or crop != crop.clamped():
                    continue
                valid[mode] = crop
            except (KeyError, TypeError, ValueError):
                continue
        if valid:
            result[name] = valid
    return result

def save_crop(source, mode, crop, aspect=None):
    source = Path(source)
    if mode not in ("Web", "Print"):
        raise ValueError("Unknown crop mode")
    data = _read(source.parent)
    modes = data["images"].get(source.name, {})
    if not isinstance(modes, dict):
        modes = {}
    if crop is None:
        modes.pop(mode, None)
    else:
        record = asdict(crop.clamped())
        if aspect is not None and math.isfinite(aspect) and aspect > 0:
            record["aspect"] = aspect
        modes[mode] = record
    if modes:
        data["images"][source.name] = modes
    else:
        data["images"].pop(source.name, None)
    path = source.parent / FILENAME
    if not data["images"] and not path.exists():
        return
    fd, temporary = tempfile.mkstemp(prefix=".freeda-crops-", suffix=".tmp", dir=source.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as handle:
            json.dump(data,handle,ensure_ascii=False,indent=2,allow_nan=False)
            handle.write("\n")
        os.replace(temporary,path)
    finally:
        Path(temporary).unlink(missing_ok=True)
