"""Rule-of-thirds overlay clipped to the same image windows as the export."""
from PIL import Image, ImageDraw, ImageChops
from .geometry import frame_geometry_for_total_width
from .models import CaptionMode, LayoutMode, PrintRenderOptions
from .logos import load_logo, logo_layout
from .render import crop_eye, _font, _caption_metrics, _fit_lrl_caption
from .cropping import fit_linked_crop
from .eye_shapes import eye_mask


def crop_grid(image, source, options):
    result = image.convert("RGBA")
    if isinstance(options, PrintRenderOptions):
        from .print_layout import print_layout
        boxes = print_layout(options).eye_boxes(options.dpi, options.bleed_mm)
    else:
        count = 3 if options.layout == LayoutMode.LRL else 2
        rows = 2 if options.layout == LayoutMode.BOTH else 1
        geom = frame_geometry_for_total_width(image.width, options.frame_percent, count)
        frame, eye_w = geom.frame_px, geom.eye_width
        left = source.crop((0, 0, source.width // 2, source.height))
        eye = crop_eye(left, fit_linked_crop(left.size, options.crop, options.eye_aspect))
        eye_h = max(1, round(eye_w * eye.height / eye.width))
        font = _font(options.font_family, max(9, round(eye_w * options.caption_size_percent / 100)))
        caption = options.caption
        if count == 3:
            caption, font = _fit_lrl_caption(caption, font, options.font_family, eye_w)
        _, _, caption_h = _caption_metrics(caption, font, eye_w)
        caption_band = caption_h + max(1, round(font.size * .4)) + max(1, round(font.size * .6)) if caption else 0
        if options.caption_mode == CaptionMode.LOGO:
            footer = logo_layout(load_logo(options.logo_path).size, eye_w, options.logo_height_percent)
            caption_band = max(1, round(footer.height)) + max(1, round(footer.gap_top)) + max(1, round(footer.gap_bottom))
        row_step = eye_h + caption_band + frame
        boxes = []
        for row in range(rows):
            for index in range(count):
                x = frame + index * (eye_w + frame)
                width = image.width - x if frame == 0 and index == count - 1 else eye_w
                y = frame + row * row_step
                boxes.append((x, y, x + width, y + eye_h))
    for x0, y0, x1, y1 in boxes:
        width, height = x1 - x0, y1 - y0
        overlay = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(overlay)
        for fraction in (1 / 3, 2 / 3):
            vx, hy = round(width * fraction), round(height * fraction)
            for points in ((vx, 0, vx, height - 1), (0, hy, width - 1, hy)):
                draw.line(points, fill=(0, 0, 0, 130), width=3)
                draw.line(points, fill=(255, 255, 255, 200), width=1)
        mask = eye_mask(overlay.size, round(width * options.inner_radius_percent / 100),
                        options.eye_shape, options.arch_height_percent)
        mask = ImageChops.multiply(mask, image.convert("RGBA").getchannel("A").crop((x0,y0,x1,y1)))
        overlay.putalpha(ImageChops.multiply(overlay.getchannel("A"), mask))
        result.alpha_composite(overlay, (x0, y0))
    result.putalpha(image.convert("RGBA").getchannel("A"))
    return result
