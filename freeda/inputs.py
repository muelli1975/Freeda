"""One orientation-normalizing loader for preview, cropping and export."""
from pathlib import Path
from PIL import Image, ImageOps


def load_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        # Pillow also handles TIFF decoders which already apply Orientation.
        return ImageOps.exif_transpose(source).convert("RGB")


def image_size(path):
    """Read normalized dimensions without decoding pixels (TIFF is already oriented)."""
    with Image.open(path) as image:
        size = image.size
        if image.format != "TIFF" and image.getexif().get(274, 1) in (5, 6, 7, 8):
            return size[1], size[0]
        return size
