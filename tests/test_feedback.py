import tempfile
import unittest
from pathlib import Path

from PIL import Image

from freeda.batch import discover_files, render_web_batch
from freeda.geometry import frame_geometry_for_total_width, mm_to_px
from freeda.models import BatchItem, LayoutMode, OutputFormat, PrintRenderOptions, WebRenderOptions
from freeda.output import export_targets
from freeda.print_render import render_print
from freeda.render import render_web


class FeedbackTests(unittest.TestCase):
    def source(self):
        source = Image.new("RGB", (600, 200), "red")
        source.paste(Image.new("RGB", (300, 200), "lime"), (300, 0))
        return source

    def test_web_symbols_only_use_top_frame(self):
        for layout in (LayoutMode.PARALLEL, LayoutMode.CROSS, LayoutMode.BOTH):
            options = WebRenderOptions(layout=layout, target_long_edge=1280, frame_percent=3)
            geom = frame_geometry_for_total_width(1280, 3)
            eye_h = round(geom.eye_width * 2 / 3)
            result = render_web(self.source(), options)
            row_h = eye_h + 2 * geom.frame_px
            self.assertEqual(result.height, row_h if layout != LayoutMode.BOTH else 2 * row_h - geom.frame_px)
            expected = (0, 255, 0, 255) if layout == LayoutMode.CROSS else (255, 0, 0, 255)
            self.assertEqual(result.getpixel((geom.frame_px + 10, geom.frame_px)), expected)

    def test_caption_can_grow_independently(self):
        plain = render_web(self.source(), WebRenderOptions(layout=LayoutMode.PARALLEL))
        caption = render_web(self.source(), WebRenderOptions(layout=LayoutMode.PARALLEL, caption="Untertitel"))
        self.assertGreater(caption.height, plain.height)

    def test_print_image_starts_at_frame_with_bleed(self):
        options = PrintRenderOptions(width_mm=150, height_mm=100, bleed_mm=3, frame_percent=3)
        image = render_print(self.source(), options)
        frame = frame_geometry_for_total_width(mm_to_px(150, 300), 3).frame_px
        bleed = mm_to_px(3, 300)
        self.assertEqual(image.getpixel((bleed + frame + 10, bleed + frame)), (255, 0, 0, 255))

    def test_output_tree_and_rerun_overwrites_output_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "series" / "photo.png"
            source.parent.mkdir()
            self.source().save(source)
            items = discover_files([root])
            targets = export_targets(items, None, root, "web", OutputFormat.PNG)
            self.assertEqual(targets[0], root / "output/series/photo_freeda_web.png")
            render_web_batch(items, root, WebRenderOptions(target_long_edge=1280, output_format=OutputFormat.PNG), targets=targets)
            self.assertEqual(len(discover_files([root])), 1)
            second = export_targets(items, None, root, "web", OutputFormat.PNG)
            self.assertEqual(second[0], targets[0])
            original = source.read_bytes()
            first_export = targets[0].read_bytes()
            render_web_batch(items, root, WebRenderOptions(target_long_edge=1600, output_format=OutputFormat.PNG), targets=second)
            self.assertNotEqual(targets[0].read_bytes(), first_export)
            self.assertEqual(source.read_bytes(), original)
            self.assertTrue(source.exists())

    def test_same_name_and_different_extensions_get_unique_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            items = [BatchItem(root / "a/photo.jpg", Path("photo.jpg")),
                     BatchItem(root / "b/photo.jpg", Path("photo.jpg")),
                     BatchItem(root / "a/photo.png", Path("photo.png"))]
            targets = export_targets(items, root / "custom", None, "web", OutputFormat.JPEG)
            self.assertEqual(len(set(targets)), 3)
            automatic = export_targets(items[:2], None, None, "print", OutputFormat.PNG)
            self.assertEqual(automatic[0].parent, root / "a/output")
            self.assertEqual(automatic[1].parent, root / "b/output")

    def test_defaults_are_four_percent(self):
        from freeda.config import DEFAULT_FRAME_PERCENT, APP_VERSION
        from freeda import __version__
        self.assertEqual(DEFAULT_FRAME_PERCENT, 4)
        self.assertEqual(APP_VERSION, __version__)
        self.assertEqual(WebRenderOptions().frame_percent, 4)
        self.assertEqual(PrintRenderOptions().frame_percent, 4)


if __name__ == "__main__":
    unittest.main()
