"""Rule-of-thirds overlay clipped to the same image windows as the export."""
from PIL import Image, ImageDraw, ImageChops
from .models import PrintRenderOptions
from .render import crop_eye, web_geometry
from .cropping import fit_linked_crop
from .eye_shapes import eye_mask


def crop_grid(image, source, options):
    result = image.convert("RGBA")
    if isinstance(options, PrintRenderOptions):
        from .print_layout import print_layout
        boxes = print_layout(options).eye_boxes(options.dpi, options.bleed_mm)
        canvas_size = image.size
    else:
        left = source.crop((0, 0, source.width // 2, source.height))
        eye = crop_eye(left, fit_linked_crop(left.size, options.crop, options.eye_aspect))
        geometry = web_geometry(eye.size, options)
        boxes, canvas_size = geometry.eye_boxes, geometry.native_size
    canvas = Image.new("RGBA", canvas_size)
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
        overlay.putalpha(ImageChops.multiply(overlay.getchannel("A"), mask))
        canvas.alpha_composite(overlay, (x0, y0))
    if canvas.size != image.size:
        canvas = canvas.resize(image.size, Image.Resampling.LANCZOS)
    canvas.putalpha(ImageChops.multiply(canvas.getchannel("A"), result.getchannel("A")))
    result.alpha_composite(canvas)
    result.putalpha(image.convert("RGBA").getchannel("A"))
    return result
