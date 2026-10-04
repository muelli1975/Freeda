from __future__ import annotations

import unittest
from pathlib import Path

from freeda.models import BatchItem, Crop
from freeda.print_flow import CropBatchMode, PrintBatchSession


class PrintBatchFlowTests(unittest.TestCase):
    def items(self):
        return [
            BatchItem(Path("a.jpg"), Path("a.jpg")),
            BatchItem(Path("b.jpg"), Path("b.jpg")),
        ]

    def test_manual_mode_pauses_each_item(self):
        session = PrintBatchSession(self.items(), CropBatchMode.MANUAL_EACH)
        self.assertTrue(session.needs_manual_crop)
        session.accept(Crop(0.1, 0.1, 0.8, 0.8))
        self.assertTrue(session.needs_manual_crop)
        session.accept(Crop())
        self.assertTrue(session.finished)

    def test_reuse_mode_remembers_crop(self):
        session = PrintBatchSession(self.items(), CropBatchMode.REUSE)
        crop = Crop(0.1, 0.2, 0.7, 0.6)
        session.accept(crop)
        self.assertEqual(session.suggested_crop(), crop)


if __name__ == "__main__":
    unittest.main()
