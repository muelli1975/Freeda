from __future__ import annotations

from dataclasses import replace

from PIL import Image, ImageDraw

from .geometry import frame_geometry_for_total_width, mm_to_px, print_canvas_px
from .models import Crop, CuttingGuide, LayoutMode, PrintRenderOptions
from .render import (
    _draw_centered,
    _draw_caption,
    _caption_metrics,
    _fit_lrl_caption,
    _draw_symbols,
    _font,
    _rounded_eye,
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


def _bands(eye_width: int, frame: int, caption: str, family: str, symbol: str, caption_size_percent: float, eye_count: int = 2):
    symbol_font, symbol_gap = _symbol_style(family, frame, symbol)
    caption_font = _font(family, max(9, round(eye_width * caption_size_percent / 100)))
    if eye_count == 3:
        caption, caption_font = _fit_lrl_caption(caption, caption_font, family, eye_width)
    _, _, caption_h = _caption_metrics(caption, caption_font, eye_width)
    caption_gap = max(frame, round(eye_width * 0.010)) if caption else 0
    symbol_band = 0
    caption_band = caption_h + 2 * caption_gap if caption else 0
    return symbol_font, caption_font, symbol_gap, caption_gap, symbol_band, caption_band


def print_eye_aspect(options: PrintRenderOptions) -> float:
    """Return the aspect ratio of the printed image area of one stereo half."""
    trim_w = mm_to_px(options.width_mm, options.dpi)
    trim_h = mm_to_px(options.height_mm, options.dpi)
    geom = frame_geometry_for_total_width(trim_w, options.frame_percent, 3 if options.layout == LayoutMode.LRL else 2)
    row_h = trim_h if options.layout != LayoutMode.BOTH else (trim_h + geom.frame_px * (2 if options.caption else 1)) // 2
    _, _, _, _, symbol_band, caption_band = _bands(
        geom.eye_width, geom.frame_px, options.caption, options.font_family, "II", options.caption_size_percent, 3 if options.layout == LayoutMode.LRL else 2
    )
    if options.caption and options.layout != LayoutMode.BOTH:
        caption_band -= geom.frame_px
    eye_h = max(1, row_h - 2 * geom.frame_px - symbol_band - caption_band)
    return geom.eye_width / eye_h


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


def _fixed_row(
    left: Image.Image,
    right: Image.Image,
    *,
    width: int,
    height: int,
    options: PrintRenderOptions,
    symbol: str,
    final_row: bool = False,
) -> Image.Image:
    eye_count = 3 if options.layout == LayoutMode.LRL else 2
    geom = frame_geometry_for_total_width(width, options.frame_percent, eye_count)
    eye_w, frame = geom.eye_width, geom.frame_px
    symbol_font, caption_font, symbol_gap, caption_gap, symbol_band, caption_band = _bands(
        eye_w, frame, options.caption, options.font_family, symbol, options.caption_size_percent, eye_count
    )
    if final_row and options.caption:
        caption_band -= frame
    eye_h = height - 2 * frame - symbol_band - caption_band
    if eye_h < 1:
        raise ValueError("Das gewählte Druckformat ist für Rahmen und Beschriftung zu niedrig.")

    target_aspect = eye_w / eye_h
    left = _fit_crop_to_aspect(left, options.crop, target_aspect).resize(
        (eye_w, eye_h), Image.Resampling.LANCZOS
    )
    right = _fit_crop_to_aspect(right, options.crop, target_aspect).resize(
        (eye_w, eye_h), Image.Resampling.LANCZOS
    )

    row = Image.new("RGBA", (width, height), options.frame_color)
    draw = ImageDraw.Draw(row)
    positions = [frame + index * (eye_w + frame) for index in range(eye_count)]
    image_y = frame + symbol_band
    radius = max(0, round(eye_w * max(0.0, options.inner_radius_percent) / 100.0))
    eyes = (left, right, left) if eye_count == 3 else (left, right)
    for x, eye in zip(positions, eyes):
        row.alpha_composite(_rounded_eye(eye, radius), (x, image_y))
    _draw_symbols(draw, positions, eye_w, frame, options.font_family, symbol, options.accent_color)
    if options.caption:
        caption = options.caption
        if eye_count == 3:
            caption, _ = _fit_lrl_caption(caption, caption_font, options.font_family, eye_w, shrink=False)
        caption_y = image_y + eye_h + caption_gap
        for x in positions:
            _draw_caption(draw, caption, x + eye_w // 2, caption_y, caption_font, options.accent_color, eye_w)
    return row


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
    left, right = split_full_sbs(source)
    trim_w = mm_to_px(options.width_mm, options.dpi)
    trim_h = mm_to_px(options.height_mm, options.dpi)
    canvas_w, canvas_h = print_canvas_px(
        options.width_mm, options.height_mm, options.dpi, options.bleed_mm
    )
    bleed = mm_to_px(options.bleed_mm, options.dpi)

    geom = frame_geometry_for_total_width(trim_w, options.frame_percent)
    rows: list[Image.Image] = []
    if options.layout == LayoutMode.BOTH:
        first_h = (trim_h + geom.frame_px * (2 if options.caption else 1)) // 2
        second_h = trim_h + geom.frame_px - first_h
        rows.append(_fixed_row(left, right, width=trim_w, height=first_h, options=options, symbol="II"))
        rows.append(_fixed_row(right, left, width=trim_w, height=second_h, options=options, symbol="X", final_row=True))
        trim = Image.new("RGBA", (trim_w, trim_h), options.frame_color)
        trim.alpha_composite(rows[0], (0, 0))
        trim.alpha_composite(rows[1], (0, first_h - geom.frame_px))
    elif options.layout == LayoutMode.CROSS:
        trim = _fixed_row(right, left, width=trim_w, height=trim_h, options=options, symbol="X", final_row=True)
    else:
        trim = _fixed_row(left, right, width=trim_w, height=trim_h, options=options, symbol="II", final_row=True)

    canvas = Image.new("RGBA", (canvas_w, canvas_h), options.frame_color)
    canvas.alpha_composite(trim, (bleed, bleed))
    _draw_cutting_guides(
        canvas,
        trim_box=(bleed, bleed, bleed + trim_w, bleed + trim_h),
        options=options,
    )
    return canvas
