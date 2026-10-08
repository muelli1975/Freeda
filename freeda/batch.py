from __future__ import annotations

import os
import re
from dataclasses import dataclass, field, replace
from threading import Event
from pathlib import Path
from typing import Iterable

from PIL import Image

from .jobs import Cancelled, check_cancel
from .models import BatchItem, Crop, PrintRenderOptions, WebRenderOptions
from .print_render import render_print
from .render import render_web, save_render

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def discover_files(paths: Iterable[Path], *, recursive: bool = True,
                   exclude: Iterable[Path] = (), cancel: Event | None = None) -> list[BatchItem]:
    """Freeze inputs before export; prune generated trees before descending."""
    raw_paths = list(dict.fromkeys(Path(p).resolve() for p in paths))
    roots = [p for p in raw_paths if p.is_dir()]
    if recursive:
        roots = [p for p in roots if not any(q in p.parents for q in roots)]
    blocked_roots = tuple(Path(p).resolve() for p in exclude)
    items, seen = [], set()

    def blocked(path, root):
        resolved = path.resolve()
        return any(q != root and q.is_relative_to(root) and (q == resolved or q in resolved.parents)
                   for q in blocked_roots)

    def add(path, root=None):
        resolved = path.resolve()
        if resolved in seen or path.suffix.lower() not in SUPPORTED_EXTENSIONS or not path.is_file():
            return
        seen.add(resolved)
        relative = path.relative_to(root) if root else Path(path.name)
        items.append(BatchItem(path, relative, root))

    def failed(error):
        raise error

    for root in roots:
        check_cancel(cancel)
        for directory, dirs, names in os.walk(root, followlinks=False, onerror=failed):
            check_cancel(cancel)
            folder = Path(directory)
            dirs[:] = sorted(n for n in dirs if n.casefold() not in {"output", "tmp", "_temp"}
                and not (folder / n).is_symlink() and not (folder / n).is_junction()
                and not blocked(folder / n, root))
            for name in sorted(names, key=natural_key):
                check_cancel(cancel)
                child = folder / name
                if not child.is_symlink() and not blocked(child, root) and not is_generated(child):
                    add(child, root)
            if not recursive:
                break
    # Explicit files remain selectable, including a deliberately reopened export.
    for path in raw_paths:
        check_cancel(cancel)
        if path.is_file():
            add(path)
    return sorted(items, key=lambda item: natural_key(str(item.source)))


def natural_key(name):
    return tuple((0, int(part)) if part.isdigit() else (1, part.casefold())
                 for part in re.split(r"(\d+)", name))


def is_generated(path: Path) -> bool:
    return bool(re.search(r"_freeda_(?:web|print)(?:_\d+)?$", path.stem, re.IGNORECASE)
                or path.name.startswith(".freeda-export-"))


def render_web_batch(
    items: Iterable[BatchItem],
    output_root: Path,
    options: WebRenderOptions,
    *,
    caption_from_filename: bool = False,
    overwrite: bool = True,
    progress=None,
    targets: list[Path] | None = None,
    crops: dict[Path, object] | None = None,
    metadata_warnings: list[str] | None = None,
) -> list[Path]:
    written: list[Path] = []
    item_list = list(items)
    for index, item in enumerate(item_list, start=1):
        caption = item.source.stem if caption_from_filename else options.caption
        current = WebRenderOptions(**{**options.__dict__, "caption": caption,
            "crop": crops.get(item.source.resolve(), options.crop) if crops is not None else options.crop})
        suffix = ".png" if current.output_format.value == "png" else ".jpg"
        target = targets[index - 1] if targets is not None else Path(output_root) / item.relative_path.with_suffix(suffix)
        if target.exists() and not overwrite:
            continue
        with Image.open(item.source) as source:
            source.load()
            rendered = render_web(source.convert("RGB"), current)
        metadata = save_render(rendered, target, current.output_format,
            background_color="#000000", metadata_source=item.source)
        if not metadata.success and metadata_warnings is not None:
            metadata_warnings.append(f"{item.source.name}: {metadata.message}")
        written.append(target)
        if progress:
            progress(index, len(item_list), item)
    return written


@dataclass
class BatchResult:
    written: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    completed: int = 0
    skipped: int = 0
    cancelled: bool = False


def run_batch(items, targets, options, *, cancel: Event, crops=None,
              review=False, reuse=False, choose_crop=None, progress=None, crop_applied=None) -> BatchResult:
    """One worker for Web and Print; crop requests pause this worker only."""
    items, targets = list(items), list(targets)
    if len(items) != len(targets):
        raise ValueError("Für jedes Eingabebild wird genau ein Ausgabeziel benötigt.")
    if {str(p.resolve()).casefold() for p in targets} & {str(i.source.resolve()).casefold() for i in items}:
        raise ValueError("Originaldatei darf nicht verändert werden.")
    crops = crops or {}
    result = BatchResult()
    shared = None
    for index, (item, target) in enumerate(zip(items, targets), 1):
        try:
            check_cancel(cancel)
            if progress:
                progress(index - 1, len(items), item)
            with Image.open(item.source) as source:
                source.load()
                image = source.convert("RGB")
            check_cancel(cancel)
            key = item.source.resolve()
            crop = crops.get(key, options.crop)
            if reuse and shared is not None:
                crop = shared
            elif choose_crop is not None and (review or key not in crops):
                action, crop = choose_crop(item, image, replace(options, crop=crop), index, len(items))
                check_cancel(cancel)
                if action == "cancel":
                    raise Cancelled()
                if action == "skip":
                    result.skipped += 1
                    continue
                crop = crop or Crop()
            shared = crop
            if crop_applied is not None:
                crop_applied(item, crop)
            current = replace(options, crop=crop)
            check_cancel(cancel)
            printed = isinstance(current, PrintRenderOptions)
            rendered = render_print(image, current) if printed else render_web(image, current)
            check_cancel(cancel)
            metadata = save_render(rendered, target, current.output_format,
                dpi=current.dpi if printed else None,
                background_color="#ffffff" if printed else "#000000",
                metadata_source=item.source, cancel=cancel)
            result.written.append(target)
            if metadata is not None and not metadata.success:
                result.warnings.append(f"{item.source}: {metadata.message}")
        except Cancelled:
            result.cancelled = True
            break
        except Exception as error:
            result.errors.append(f"{item.source}: {error}")
        finally:
            if not result.cancelled:
                result.completed = index
                if progress:
                    progress(index, len(items), item)
    return result
