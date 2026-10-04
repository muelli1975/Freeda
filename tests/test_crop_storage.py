import json
import shutil
import tempfile
import unittest
from pathlib import Path
from freeda.crop_storage import FILENAME, load_crops, save_crop
from freeda.models import Crop

class CropStorageTests(unittest.TestCase):
    def test_relative_roundtrip_and_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "pictures"
            folder.mkdir()
            source = folder / "stereo.png"
            source.write_bytes(b"original image")
            crop = Crop(.1, .2, .7, .6)
            save_crop(source, "Web", crop, 4/3)
            save_crop(source, "Print", Crop(.2, .1, .5, .8), 1)
            save_crop(folder/"other.png", "Web", Crop())
            data = json.loads((folder/FILENAME).read_text())
            self.assertEqual(data["images"][source.name]["Web"]["aspect"], 4/3)
            self.assertNotIn(str(folder), (folder/FILENAME).read_text())
            self.assertEqual(source.read_bytes(), b"original image")
            moved = root / "moved"
            shutil.move(str(folder), str(moved))
            self.assertEqual(load_crops(moved)[source.name]["Web"], crop)
            save_crop(moved/source.name,"Web",None)
            records = load_crops(moved)
            self.assertNotIn("Web", records[source.name])
            self.assertIn("Print",records[source.name])
            self.assertIn("other.png", records)

    def test_corrupt_file_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root/FILENAME
            path.write_text("broken JSON")
            with self.assertRaises(ValueError):
                load_crops(root)
            with self.assertRaises(ValueError):
                save_crop(root/"one.png","Web",Crop())
            self.assertEqual(path.read_text(),"broken JSON")

    def test_invalid_records_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = {"version":1,"images":{
                "../outside.png":{"Web":{"x":0,"y":0,"width":1,"height":1}},
                "bad.png":{"Web":{"x":0,"y":0,"width":-1,"height":1}},
                "valid.png":{"Web":{"x":0,"y":0,"width":1,"height":1}}}}
            (root/FILENAME).write_text(json.dumps(data))
            self.assertEqual(load_crops(root), {"valid.png":{"Web":Crop()}})

    def test_reset_without_record_does_not_create_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            save_crop(root/"one.png","Web",None)
            self.assertFalse((root/FILENAME).exists())
