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


def render_preview(source, request):
    """Render a frozen GUI snapshot without reading widgets or changing options."""
    from .models import LayoutMode
    from .render import render_web, split_full_sbs, crop_eye
    from .crop_grid import crop_grid
    options, width, height = request.options, request.width, request.height
    if request.view == "anaglyph":
        return anaglyph_crop_preview(source, request)
    if request.view is not None:
        options = replace(options, layout=LayoutMode.CROSS if request.view == "cross" else LayoutMode.PARALLEL)
    if isinstance(options, PrintRenderOptions):
        options = print_preview_options(options, width, height)
        from .print_render import render_print
        rendered = render_print(source, options)
        if request.grid:
            rendered = crop_grid(rendered, source, options)
        if not request.show_bleed:
            bleed = mm_to_px(options.bleed_mm, options.dpi)
            w, h = mm_to_px(options.width_mm, options.dpi), mm_to_px(options.height_mm, options.dpi)
            rendered = rendered.crop((bleed, bleed, bleed+w, bleed+h))
    else:
        options = replace(options, target_long_edge=max(16, min(max(width, height),
                          options.target_long_edge or max(source.size))))
        rendered = render_web(source, options)
        if request.grid:
            rendered = crop_grid(rendered, source, options)
    return fit_preview(preview_export_image(rendered, options), width, height)


def anaglyph_crop_preview(source, request):
    """Show one framed control image using the export's existing renderers."""
    import numpy as np
    from .anaglyph import make_anaglyph
    from .models import Crop, CuttingGuide
    from .render import split_full_sbs, crop_eye, web_geometry, render_web
    from .cropping import fit_linked_crop
    from .print_layout import print_layout
    from .print_render import render_print, _fit_crop_to_aspect
    from .eye_shapes import round_outer_corners
    from .crop_grid import crop_grid

    width, height = max(1, request.width), max(1, request.height)
    original = request.options
    left, right = split_full_sbs(source)
    if isinstance(original, PrintRenderOptions):
        physical = print_layout(original)
        left = _fit_crop_to_aspect(left, original.crop, physical.eye_aspect)
        right = _fit_crop_to_aspect(right, original.crop, physical.eye_aspect)
        count, rows = len(physical.x_mm), len(physical.y_mm)
        options = print_preview_options(original, min(3200, width * count), min(3200, height * rows))
        options = replace(options, crop=Crop(), show_symbols=False, outer_radius_percent=0,
                          bleed_mm=0, cutting_guide=CuttingGuide.NONE)
        geometry = print_layout(options)
        x0, y0, x1, y1 = geometry.eye_boxes(options.dpi)[0]
        size = (x1 - x0, y1 - y0)
    else:
        crop = fit_linked_crop(left.size, original.crop, original.eye_aspect)
        left, right = crop_eye(left, crop), crop_eye(right, crop)
        factor = min(1., 1600 / max(left.size), width / left.width, height / left.height)
        size = (max(1, round(left.width * factor)), max(1, round(left.height * factor)))
        options = replace(original, crop=Crop(), eye_aspect=None, target_long_edge=None,
                          show_symbols=False, outer_radius_percent=0)
        geometry = web_geometry(size, options)
        x0, y0, x1, y1 = geometry.eye_boxes[0]

    left = left.resize(size, Image.Resampling.LANCZOS)
    right = right.resize(size, Image.Resampling.LANCZOS)
    anaglyph = Image.fromarray(make_anaglyph(np.asarray(left), np.asarray(right)))
    paired = Image.new("RGB", (anaglyph.width * 2, anaglyph.height))
    paired.paste(anaglyph, (0, 0))
    paired.paste(anaglyph, (anaglyph.width, 0))
    framed = render_print(paired, options) if isinstance(options, PrintRenderOptions) else render_web(paired, options)
    if request.grid:
        framed = crop_grid(framed, paired, options)

    if isinstance(options, PrintRenderOptions):
        bottom = framed.height
        if len(geometry.y_mm) > 1:
            boundary = geometry.y_mm[1]
            if options.margins is not None:
                boundary -= options.margins.row_gap_mm
            bottom = mm_to_px(boundary, options.dpi)
    else:
        bottom = min(framed.height, geometry.row.height)
    single = framed.crop((0, 0, min(framed.width, x1 + x0), bottom))
    radius = round(framed.width * max(0., original.outer_radius_percent) / 100)
    single = round_outer_corners(single, radius)
    return fit_preview(preview_export_image(single, original), width, height)


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

