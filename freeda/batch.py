from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image

from .models import BatchItem, WebRenderOptions
from .render import render_web, save_render

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def discover_files(paths: Iterable[Path], *, recursive: bool = True) -> list[BatchItem]:
    items: list[BatchItem] = []
    seen: set[Path] = set()

    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            resolved = path.resolve()
            if resolved not in seen:
                items.append(BatchItem(source=path, relative_path=Path(path.name)))
                seen.add(resolved)
            continue

        if path.is_dir():
            iterator = path.rglob("*") if recursive else path.glob("*")
            for child in sorted(iterator):
                if "output" in (part.casefold() for part in child.relative_to(path).parts[:-1]):
                    continue
                if not child.is_file() or child.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                resolved = child.resolve()
                if resolved in seen:
                    continue
                items.append(BatchItem(source=child, relative_path=child.relative_to(path)))
                seen.add(resolved)

    return items


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
            background_color=current.frame_color, metadata_source=item.source)
        if not metadata.success and metadata_warnings is not None:
            metadata_warnings.append(f"{item.source.name}: {metadata.message}")
        written.append(target)
        if progress:
            progress(index, len(item_list), item)
    return written
