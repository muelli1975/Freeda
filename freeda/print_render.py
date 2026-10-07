from __future__ import annotations

from dataclasses import replace

from PIL import Image, ImageDraw

from .geometry import mm_to_px, print_canvas_px
from .models import Crop, CuttingGuide, LayoutMode, PrintRenderOptions
from .print_layout import print_layout
from .eye_shapes import shape_eye, round_outer_corners
from .logos import load_logo
from .render import (
    _draw_centered,
    _font,
    _text_height,
    _symbol_style,
    crop_eye,
    split_full_sbs,
)


def crop_for_aspect(
    image_size: tuple[int, int],
    target_aspect: float,
    *,
    zoom: float = 1.0,
    position_x: float = 0.5,
    position_y: float = 0.5,
) -> Crop:
    """Create a linked normalized crop for one eye at a fixed output aspect."""
    width, height = image_size
    if width < 1 or height < 1 or target_aspect <= 0:
        return Crop()

    source_aspect = width / height
    if source_aspect >= target_aspect:
        base_h = 1.0
        base_w = target_aspect / source_aspect
    else:
        base_w = 1.0
        base_h = source_aspect / target_aspect

    zoom = max(1.0, min(4.0, float(zoom)))
    crop_w = base_w / zoom
    crop_h = base_h / zoom
    px = max(0.0, min(1.0, float(position_x)))
    py = max(0.0, min(1.0, float(position_y)))
    x = (1.0 - crop_w) * px
    y = (1.0 - crop_h) * py
    return Crop(x=x, y=y, width=crop_w, height=crop_h).clamped()


def print_eye_aspect(options: PrintRenderOptions) -> float:
    """Return the aspect ratio of the printed image area of one stereo half."""
    return print_layout(options).eye_aspect


def _fit_crop_to_aspect(image: Image.Image, crop: Crop, target_aspect: float) -> Image.Image:
    cropped = crop_eye(image, crop)
    w, h = cropped.size
    aspect = w / h
    if abs(aspect - target_aspect) < 1e-6:
        return cropped
    if aspect > target_aspect:
        target_w = max(1, round(h * target_aspect))
        x = max(0, (w - target_w) // 2)
        return cropped.crop((x, 0, x + target_w, h))
    target_h = max(1, round(w / target_aspect))
    y = max(0, (h - target_h) // 2)
    return cropped.crop((0, y, w, y + target_h))


def _draw_cutting_guides(
    image: Image.Image,
    *,
    trim_box: tuple[int, int, int, int],
    options: PrintRenderOptions,
) -> None:
    if options.cutting_guide == CuttingGuide.NONE:
        return
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = trim_box
    color = "#808080"
    line_w = max(1, mm_to_px(0.2, options.dpi))

    if options.cutting_guide == CuttingGuide.LINE:
        draw.rectangle((left, top, right - 1, bottom - 1), outline=color, width=line_w)
        return

    # Classic crop marks stay in the bleed area and do not cross into the card.
    bleed = min(left, top, image.width - right, image.height - bottom)
    if bleed <= 0:
        return
    length = max(line_w * 4, min(bleed, mm_to_px(3.0, options.dpi)))
    gap = max(line_w * 2, mm_to_px(0.6, options.dpi))
    segments = [
        ((left - gap - length, top), (left - gap, top)),
        ((left, top - gap - length), (left, top - gap)),
        ((right + gap, top), (right + gap + length, top)),
        ((right, top - gap - length), (right, top - gap)),
        ((left - gap - length, bottom), (left - gap, bottom)),
        ((left, bottom + gap), (left, bottom + gap + length)),
        ((right + gap, bottom), (right + gap + length, bottom)),
        ((right, bottom + gap), (right, bottom + gap + length)),
    ]
    for a, b in segments:
        draw.line((a, b), fill=color, width=line_w)


def render_print(source: Image.Image, options: PrintRenderOptions) -> Image.Image:
    geometry = print_layout(options)
    left, right = split_full_sbs(source)
    trim_w = mm_to_px(options.width_mm, options.dpi)
    trim_h = mm_to_px(options.height_mm, options.dpi)
    canvas_w, canvas_h = print_canvas_px(
        options.width_mm, options.height_mm, options.dpi, options.bleed_mm
    )
    bleed = mm_to_px(options.bleed_mm, options.dpi)

    trim = Image.new("RGBA", (trim_w, trim_h), options.frame_color)
    draw = ImageDraw.Draw(trim)
    boxes = geometry.eye_boxes(options.dpi)
    count = len(geometry.x_mm)
    caption_font = _font(options.font_family, max(1, mm_to_px(geometry.caption_font_mm, options.dpi)))
    logo = None
    if geometry.logo_height_mm > 0:
        logo = load_logo(options.logo_path).resize((max(1, mm_to_px(geometry.logo_width_mm, options.dpi)),
                                                  max(1, mm_to_px(geometry.logo_height_mm, options.dpi))), Image.Resampling.LANCZOS)
    for row_index, y_mm in enumerate(geometry.y_mm):
        crossed = options.layout == LayoutMode.CROSS or (options.layout == LayoutMode.BOTH and row_index == 1)
        eyes = (right, left) if crossed else ((left, right, left) if count == 3 else (left, right))
        row_boxes = boxes[row_index * count:(row_index + 1) * count]
        for eye, box in zip(eyes, row_boxes):
            x0, y0, x1, y1 = box
            cropped = _fit_crop_to_aspect(eye, options.crop, geometry.eye_aspect)
            resized = cropped.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
            radius = round((x1 - x0) * max(0, options.inner_radius_percent) / 100)
            bottom_radius = None if options.bottom_radius_percent is None else round(
                (x1 - x0) * max(0, options.bottom_radius_percent) / 100)
            trim.alpha_composite(shape_eye(resized, radius, options.eye_shape, options.arch_height_percent,
                                          bottom_radius=bottom_radius), (x0, y0))
        band = mm_to_px(geometry.symbol_bands_mm[row_index], options.dpi)
        if options.show_symbols and band > 0:
            symbol = "X" if crossed else "II"
            markers = [(round((box[0] + box[2]) / 2), symbol) for box in row_boxes]
            if count == 3:
                markers = [(round((row_boxes[i - 1][2] + row_boxes[i][0]) / 2), mark)
                           for i, mark in ((1, "II"), (2, "X"))]
            for centre, mark in markers:
                font, offset_y = _symbol_style(band, mark)
                if _text_height(font, mark) <= band:
                    _draw_centered(draw, mark, centre, mm_to_px(y_mm, options.dpi) - band + offset_y,
                                   font, options.accent_color)
        if logo is not None:
            text_y = mm_to_px(y_mm + geometry.eye_height_mm + geometry.caption_top_mm, options.dpi)
            for box in row_boxes:
                trim.alpha_composite(logo, (round((box[0]+box[2]-logo.width)/2), text_y))
        elif geometry.caption_lines:
            for box in row_boxes:
                for line_index, line in enumerate(geometry.caption_lines):
                    text_y = mm_to_px(y_mm + geometry.eye_height_mm + geometry.caption_top_mm
                                     + line_index * geometry.caption_step_mm, options.dpi)
                    _draw_centered(draw, line, round((box[0] + box[2]) / 2), text_y,
                                   caption_font, options.accent_color)

    canvas = Image.new("RGBA", (canvas_w, canvas_h), options.frame_color)
    canvas.alpha_composite(trim, (bleed, bleed))
    _draw_cutting_guides(
        canvas,
        trim_box=(bleed, bleed, bleed + trim_w, bleed + trim_h),
        options=options,
    )
    radius = round(canvas.width * max(0, options.outer_radius_percent) / 100)
    return round_outer_corners(canvas, radius)
