from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import BatchItem, Crop


class CropBatchMode(str, Enum):
    MANUAL_EACH = "manual_each"
    REUSE = "reuse"


@dataclass
class PrintBatchSession:
    items: list[BatchItem]
    mode: CropBatchMode = CropBatchMode.MANUAL_EACH
    index: int = 0
    last_crop: Crop = Crop()

    @property
    def finished(self) -> bool:
        return self.index >= len(self.items)

    @property
    def current(self) -> BatchItem | None:
        if self.finished:
            return None
        return self.items[self.index]

    @property
    def needs_manual_crop(self) -> bool:
        return not self.finished and self.mode == CropBatchMode.MANUAL_EACH

    def suggested_crop(self) -> Crop:
        return self.last_crop if self.mode == CropBatchMode.REUSE else Crop()

    def accept(self, crop: Crop) -> BatchItem:
        if self.finished:
            raise IndexError("Print-Batch ist bereits abgeschlossen.")
        item = self.items[self.index]
        self.last_crop = crop.clamped()
        self.index += 1
        return item

    def skip(self) -> BatchItem:
        if self.finished:
            raise IndexError("Print-Batch ist bereits abgeschlossen.")
        item = self.items[self.index]
        self.index += 1
        return item
