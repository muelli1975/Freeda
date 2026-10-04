from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .fonts import resolve_font
from .geometry import frame_geometry_for_total_width
from .models import Crop, LayoutMode, OutputFormat, WebRenderOptions


def split_full_sbs(image: Image.Image) -> tuple[Image.Image, Image.Image]:
    width, height = image.size
    half = width // 2
    if half < 1:
        raise ValueError("Das Side-by-Side-Bild ist zu schmal.")
    left = image.crop((0, 0, half, height))
    right = image.crop((half, 0, half * 2, height))
    return left, right


def crop_eye(image: Image.Image, crop: Crop) -> Image.Image:
    c = crop.clamped()
    width, height = image.size
    left = int(round(c.x * width))
    top = int(round(c.y * height))
    right = int(round((c.x + c.width) * width))
    bottom = int(round((c.y + c.height) * height))
    right = max(left + 1, min(width, right))
    bottom = max(top + 1, min(height, bottom))
    return image.crop((left, top, right, bottom))


def _font(family: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    target = resolve_font(family)
    if target:
        try:
            return ImageFont.truetype(target, max(8, int(size)))
        except OSError:
            pass
    return ImageFont.load_default()


def _text_height(font: ImageFont.ImageFont, text: str) -> int:
    box = font.getbbox(text or "Ag")
    return max(1, box[3] - box[1])


def _draw_centered(draw: ImageDraw.ImageDraw, text: str, center_x: int, y: int, font, fill: str) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    draw.text((center_x - width / 2, y - box[1]), text, font=font, fill=fill)


def _rounded_eye(image: Image.Image, radius: int) -> Image.Image:
    image = image.convert("RGBA")
    if radius <= 0:
        return image
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width - 1, image.height - 1), radius=radius, fill=255)
    image.putalpha(mask)
    return image


def _row(
    left: Image.Image,
    right: Image.Image,
    *,
    total_width: int,
    frame_percent: float,
    frame_color: str,
    accent_color: str,
    symbol: str,
    caption: str,
    font_family: str,
    inner_radius_percent: float,
) -> Image.Image:
    geom = frame_geometry_for_total_width(total_width, frame_percent)
    eye_w = geom.eye_width
    frame = geom.frame_px

    aspect = left.height / left.width
    eye_h = max(1, int(round(eye_w * aspect)))
    left = left.resize((eye_w, eye_h), Image.Resampling.LANCZOS)
    right = right.resize((eye_w, eye_h), Image.Resampling.LANCZOS)

    symbol_font = _font(font_family, max(10, round(eye_w * 0.050)))
    caption_font = _font(font_family, max(9, round(eye_w * 0.035)))
    symbol_h = _text_height(symbol_font, symbol)
    caption_h = _text_height(caption_font, caption) if caption else 0

    symbol_gap = max(frame, round(eye_w * 0.012))
    caption_gap = max(frame, round(eye_w * 0.010)) if caption else 0
    symbol_band = symbol_h + 2 * symbol_gap
    caption_band = caption_h + 2 * caption_gap if caption else 0

    height = frame + symbol_band + eye_h + caption_band + frame
    row = Image.new("RGBA", (total_width, height), frame_color)
    draw = ImageDraw.Draw(row)

    x1 = frame
    x2 = frame + eye_w + frame
    image_y = frame + symbol_band

    radius = max(0, round(eye_w * max(0.0, inner_radius_percent) / 100.0))
    row.alpha_composite(_rounded_eye(left, radius), (x1, image_y))
    row.alpha_composite(_rounded_eye(right, radius), (x2, image_y))

    symbol_y = frame + symbol_gap
    _draw_centered(draw, symbol, x1 + eye_w // 2, symbol_y, symbol_font, accent_color)
    _draw_centered(draw, symbol, x2 + eye_w // 2, symbol_y, symbol_font, accent_color)

    if caption:
        caption_y = image_y + eye_h + caption_gap
        _draw_centered(draw, caption, x1 + eye_w // 2, caption_y, caption_font, accent_color)
        _draw_centered(draw, caption, x2 + eye_w // 2, caption_y, caption_font, accent_color)

    return row


def render_web(source: Image.Image, options: WebRenderOptions) -> Image.Image:
    left, right = split_full_sbs(source)
    left = crop_eye(left, options.crop)
    right = crop_eye(right, options.crop)

    if options.target_width is None:
        # Preserve the two source-eye widths and add the proportional frame.
        fraction = max(0.0, options.frame_percent) / 100.0
        target_width = int(round(left.width * (2.0 + 3.0 * fraction)))
        if target_width % 2 == 1:
            target_width += 1
    else:
        target_width = int(options.target_width)

    rows: list[Image.Image] = []
    if options.layout in (LayoutMode.BOTH, LayoutMode.PARALLEL):
        rows.append(_row(
            left, right,
            total_width=target_width,
            frame_percent=options.frame_percent,
            frame_color=options.frame_color,
            accent_color=options.accent_color,
            symbol="II",
            caption=options.caption,
            font_family=options.font_family,
            inner_radius_percent=options.inner_radius_percent,
        ))
    if options.layout in (LayoutMode.BOTH, LayoutMode.CROSS):
        rows.append(_row(
            right, left,
            total_width=target_width,
            frame_percent=options.frame_percent,
            frame_color=options.frame_color,
            accent_color=options.accent_color,
            symbol="X",
            caption=options.caption,
            font_family=options.font_family,
            inner_radius_percent=options.inner_radius_percent,
        ))

    if len(rows) == 1:
        result = rows[0]
    else:
        frame = frame_geometry_for_total_width(target_width, options.frame_percent).frame_px
        height = sum(row.height for row in rows) - frame * (len(rows) - 1)
        result = Image.new("RGBA", (target_width, height), options.frame_color)
        y = 0
        for index, row in enumerate(rows):
            result.alpha_composite(row, (0, y))
            y += row.height
            if index + 1 < len(rows):
                y -= frame

    radius = max(0, round(result.width * max(0.0, options.outer_radius_percent) / 100.0))
    if radius > 0:
        mask = Image.new("L", result.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, result.width - 1, result.height - 1), radius=radius, fill=255)
        result.putalpha(mask)

    return result


def save_render(image: Image.Image, path: Path, output_format: OutputFormat, *, dpi: int | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {}
    if dpi:
        kwargs["dpi"] = (dpi, dpi)
    if output_format == OutputFormat.PNG:
        image.save(path.with_suffix(".png"), format="PNG", optimize=True, **kwargs)
    else:
        # 4:4:4 = subsampling 0.  Alpha is flattened onto the frame colour by
        # the caller/rendering defaults; JPEG itself cannot carry transparency.
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, "#111111")
            background.paste(image, mask=image.getchannel("A"))
            image = background
        image.convert("RGB").save(
            path.with_suffix(".jpg"),
            format="JPEG",
            quality=90,
            subsampling=0,
            optimize=True,
            **kwargs,
        )
