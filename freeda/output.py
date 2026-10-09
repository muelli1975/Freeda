from pathlib import Path

from .models import BatchItem, OutputFormat


def export_targets(items: list[BatchItem], custom_root: Path | None,
                   input_root: Path | None, mode: str, output_format: OutputFormat) -> list[Path]:
    """Preserve each input tree; stable names overwrite previous exports only."""
    suffix = ".png" if output_format == OutputFormat.PNG else ".jpg"
    originals = {str(item.source.resolve()).casefold() for item in items}
    reserved = set()
    targets = []
    for item in items:
        source_root = item.input_root or input_root
        root = Path(custom_root) if custom_root else (source_root or item.source.parent) / "output"
        relative = item.relative_path if source_root or custom_root else Path(item.source.name)
        target = root / relative.with_name(relative.stem + "_freeda_" + mode + suffix)
        original = target
        number = 2
        while str(target.resolve()).casefold() in reserved:
            target = original.with_name(f"{original.stem}_{number}{suffix}")
            number += 1
        if str(target.resolve()).casefold() in originals:
            raise ValueError("Originaldatei darf nicht verändert werden.")
        reserved.add(str(target.resolve()).casefold())
        targets.append(target)
    return targets
