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


class EyeShape(str, Enum):
    RECTANGLE = "rectangle"
    ROUNDED = "rounded"
    TOP_ROUNDED = "top_rounded"
    ARCH = "arch"


class CaptionMode(str, Enum):
    TEXT = "text"
    LOGO = "logo"


@dataclass(frozen=True)
class PrintMargins:
    side_mm: float = 5.0
    top_mm: float = 3.0
    centre_mm: float = 2.0
    bottom_mm: float = 8.0
    row_gap_mm: float = 3.0


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
    target_long_edge: int | None = 2048
    eye_aspect: float | None = None
    frame_percent: float = 4.0
    frame_color: str = "#111111"
    accent_color: str = "#c6a95e"
    outer_radius_percent: float = 0.0
    inner_radius_percent: float = 0.0
    caption: str = ""
    font_family: str = "Segoe UI"
    caption_size_percent: float = 4.0
    output_format: OutputFormat = OutputFormat.JPEG
    crop: Crop = Crop()
    show_symbols: bool = True
    eye_shape: EyeShape = EyeShape.ROUNDED
    arch_height_percent: float = 18.0
    caption_mode: CaptionMode = CaptionMode.TEXT
    logo_path: Path | None = None
    logo_height_percent: float = 6.0
    # None preserves the bottom corners of legacy contour options.
    bottom_radius_percent: float | None = None


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
    caption_size_percent: float = 4.0
    crop: Crop = Crop()
    manual_crop_each_image: bool = True
    inner_radius_percent: float = 0.0
    output_format: OutputFormat = OutputFormat.JPEG
    cutting_guide: CuttingGuide = CuttingGuide.NONE
    show_symbols: bool = True
    outer_radius_percent: float = 0.0
    eye_shape: EyeShape = EyeShape.ROUNDED
    arch_height_percent: float = 18.0
    margins: PrintMargins | None = None
    caption_points: float | None = None
    caption_gap_top_mm: float | None = None
    caption_gap_bottom_mm: float | None = None
    caption_mode: CaptionMode = CaptionMode.TEXT
    logo_path: Path | None = None
    logo_height_percent: float = 6.0
    logo_height_mm: float | None = None
    bottom_radius_percent: float | None = None


@dataclass(frozen=True)
class BatchItem:
    source: Path
    relative_path: Path
