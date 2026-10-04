from pathlib import Path

from .models import BatchItem, OutputFormat


def export_targets(items: list[BatchItem], custom_root: Path | None,
                   input_root: Path | None, mode: str, output_format: OutputFormat) -> list[Path]:
    """Keep source trees and reserve unique names without replacing existing files."""
    suffix = ".png" if output_format == OutputFormat.PNG else ".jpg"
    reserved: set[str] = set()
    targets = []
    for item in items:
        root = custom_root or ((input_root or item.source.parent) / "output")
        relative = item.relative_path if custom_root or input_root else Path(item.source.name)
        target = root / mode / relative.with_name(relative.stem + "_freeda_" + mode + suffix)
        original = target
        number = 2
        while target.exists() or str(target.resolve()).casefold() in reserved or target.resolve() == item.source.resolve():
            target = original.with_name(f"{original.stem}_{number}{suffix}")
            number += 1
        reserved.add(str(target.resolve()).casefold())
        targets.append(target)
    return targets
