from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class LayoutMode(str, Enum):
    BOTH = "both"
    PARALLEL = "parallel"
    CROSS = "cross"
    LRL = "lrl"


class OutputFormat(str, Enum):
    JPEG = "jpeg"
    PNG = "png"


class CuttingGuide(str, Enum):
    NONE = "none"
    LINE = "line"
    MARKS = "marks"


@dataclass(frozen=True)
class Crop:
    x: float = 0.0
    y: float = 0.0
    width: float = 1.0
    height: float = 1.0

    def clamped(self) -> "Crop":
        w = min(1.0, max(0.01, self.width))
        h = min(1.0, max(0.01, self.height))
        x = min(1.0 - w, max(0.0, self.x))
        y = min(1.0 - h, max(0.0, self.y))
        return Crop(x=x, y=y, width=w, height=h)


@dataclass(frozen=True)
class WebRenderOptions:
    layout: LayoutMode = LayoutMode.BOTH
    target_width: int | None = 2048
    eye_aspect: float | None = None
    frame_percent: float = 4.0
    frame_color: str = "#111111"
    accent_color: str = "#c6a95e"
    outer_radius_percent: float = 0.0
    inner_radius_percent: float = 0.0
    caption: str = ""
    font_family: str = "Segoe UI"
    caption_size_percent: float = 3.5
    output_format: OutputFormat = OutputFormat.JPEG
    crop: Crop = Crop()
    show_symbols: bool = True


@dataclass(frozen=True)
class PrintRenderOptions:
    layout: LayoutMode = LayoutMode.PARALLEL
    width_mm: float = 148.0
    height_mm: float = 105.0
    dpi: int = 300
    bleed_mm: float = 0.0
    frame_percent: float = 4.0
    frame_color: str = "#111111"
    accent_color: str = "#c6a95e"
    caption: str = ""
    font_family: str = "Segoe UI"
    caption_size_percent: float = 3.5
    crop: Crop = Crop()
    manual_crop_each_image: bool = True
    inner_radius_percent: float = 0.0
    output_format: OutputFormat = OutputFormat.JPEG
    cutting_guide: CuttingGuide = CuttingGuide.NONE
    show_symbols: bool = True


@dataclass(frozen=True)
class BatchItem:
    source: Path
    relative_path: Path
