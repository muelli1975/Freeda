from dataclasses import replace

import math


from PIL import Image


from .models import PrintRenderOptions, OutputFormat

from .geometry import mm_to_px



def fit_preview(image: Image.Image, width: int, height: int) -> Image.Image:

    """Fit to the panel, including upscaling, while preserving aspect ratio."""

    width, height = max(1, width), max(1, height)

    scale = min(width / image.width, height / image.height)

    size = (max(1, min(width, round(image.width * scale))),

            max(1, min(height, round(image.height * scale))))

    return image.resize(size, Image.Resampling.LANCZOS)


def preview_export_image(image, options):
    """Match JPEG's opaque outer corners without flattening PNG previews."""
    if options.output_format == OutputFormat.PNG:
        return image
    from .render import flatten_for_jpeg
    return flatten_for_jpeg(image, "#ffffff" if isinstance(options, PrintRenderOptions) else "#000000")



def print_preview_options(options: PrintRenderOptions, width: int, height: int) -> PrintRenderOptions:

    """Render print previews at display resolution rather than export DPI."""

    dpi = min(max(1, width) * 25.4 / (options.width_mm + 2 * options.bleed_mm),

              max(1, height) * 25.4 / (options.height_mm + 2 * options.bleed_mm))

    return replace(options, dpi=max(36, math.ceil(dpi)))



def parse_bleed(value: str) -> float:

    try:

        number = float(value.strip().replace(",", "."))

    except ValueError:

        raise ValueError("Beschnittrand in mm: Bitte eine Zahl ab 0 eingeben.") from None

    if not math.isfinite(number) or number < 0:

        raise ValueError("Beschnittrand in mm: Bitte eine Zahl ab 0 eingeben.")

    return number



def print_preview_image(source: Image.Image, options: PrintRenderOptions, *, show_bleed=False):

    from .print_render import render_print

    image = render_print(source, options)

    if show_bleed:

        return image

    bleed = mm_to_px(options.bleed_mm, options.dpi)

    width = mm_to_px(options.width_mm, options.dpi)

    height = mm_to_px(options.height_mm, options.dpi)

    return image.crop((bleed, bleed, bleed + width, bleed + height))



def parse_dpi(value: str) -> int:

    try:

        dpi = int(value.strip())

    except (ValueError, TypeError, AttributeError):

        raise ValueError("Auflösung in dpi: Bitte eine positive ganze Zahl eingeben.") from None

    if dpi < 1:

        raise ValueError("Auflösung in dpi: Bitte eine positive ganze Zahl eingeben.")

    return dpi

