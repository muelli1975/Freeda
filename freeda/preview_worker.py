"""Latest-request worker; all image decoding/rendering stays outside Tk."""
from dataclasses import dataclass
from pathlib import Path
from threading import Condition, Thread
from PIL import Image
from .inputs import load_image


@dataclass(frozen=True)
class PreviewRequest:
    source: Path | Image.Image
    options: object
    width: int
    height: int
    show_bleed: bool = False
    view: str | None = None
    grid: bool = False


class PreviewWorker:
    def __init__(self, completed):
        self.completed = completed
        self.condition = Condition()
        self.pending = None
        self.closed = False
        self.cached_key = None
        self.cached_source = None
        self.thread = Thread(target=self._run, daemon=True, name="freeda-preview")
        self.thread.start()

    def request(self, identifier, request):
        with self.condition:
            if not self.closed:
                self.pending = (identifier, request)
                self.condition.notify()

    def close(self):
        with self.condition:
            self.closed = True
            self.pending = None
            self.condition.notify()

    def _run(self):
        from .preview import render_preview
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.closed or self.pending is not None)
                if self.closed:
                    self.cached_source = None
                    return
                identifier, request = self.pending
                self.pending = None
            try:
                if isinstance(request.source, Path):
                    info = request.source.stat()
                    key = (request.source.resolve(), info.st_size, info.st_mtime_ns)
                    if key != self.cached_key:
                        self.cached_source = load_image(request.source)
                        self.cached_key = key
                    source = self.cached_source
                else:
                    source = request.source
                with self.condition:
                    if self.closed or self.pending is not None:
                        continue
                image = render_preview(source, request)
                with self.condition:
                    current = not self.closed and self.pending is None
                if current:
                    self.completed(identifier, image, None)
            except Exception as error:
                with self.condition:
                    current = not self.closed and self.pending is None
                if current:
                    self.completed(identifier, None, str(error))
