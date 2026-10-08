"""Folder snapshots, family output layout and safe cancellable Web/Print jobs."""
from dataclasses import replace
from pathlib import Path
import tempfile
import subprocess
import sys
import time
from threading import Event, Timer
import unittest
from unittest.mock import patch

from PIL import Image

from freeda.batch import discover_files, run_batch
from freeda.crop_storage import FILENAME, load_crops, save_crop
from freeda.jobs import Cancelled
from freeda.metadata import MetadataCopyResult, copy_metadata
from freeda.models import Crop, LayoutMode, OutputFormat, PrintRenderOptions, WebRenderOptions
from freeda.output import export_targets
from freeda.render import save_render


class RecursiveBatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.input = self.base / "Urlaub"
        self.output = self.base / "Freeda" / "output"
        self.source("Tag1/bild.jpg")
        self.source("Tag2/tief/bild.jpg")
        self.options = WebRenderOptions(target_long_edge=240, layout=LayoutMode.PARALLEL)
        self.metadata = patch("freeda.metadata.copy_metadata", return_value=MetadataCopyResult(True))
        self.metadata.start()
        self.addCleanup(self.metadata.stop)

    def source(self, name):
        path = self.input / name
        path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGB", (120, 40), "red")
        image.paste("blue", (60, 0, 120, 40))
        image.save(path)
        return path

    def items_targets(self, output=None, options=None):
        options = options or self.options
        items = discover_files([self.input], exclude=[output or self.output])
        mode = "print" if isinstance(options, PrintRenderOptions) else "web"
        targets = export_targets(items, output or self.output, self.input, mode, options.output_format)
        return items, targets

    def test_program_output_contains_input_name_and_relative_tree(self):
        items, targets = self.items_targets()
        self.assertEqual(targets, [self.output / "Urlaub/Tag1/bild_freeda_web.jpg",
                                  self.output / "Urlaub/Tag2/tief/bild_freeda_web.jpg"])
        self.assertEqual([i.relative_path for i in items], [Path("Tag1/bild.jpg"), Path("Tag2/tief/bild.jpg")])

    def test_input_output_option_is_explicit_and_has_no_extra_mode_folder(self):
        items = discover_files([self.input])
        targets = export_targets(items, None, self.input, "print", OutputFormat.PNG)
        self.assertEqual(targets[0], self.input / "output/Tag1/bild_freeda_print.png")

    def test_recursion_is_optional(self):
        self.assertEqual(discover_files([self.input], recursive=False), [])
        path = self.source("at-root.png")
        self.assertEqual([i.source for i in discover_files([self.input], recursive=False)], [path])

    def test_custom_output_tree_is_pruned_before_descending(self):
        output = self.input / "Tag1/exportiert"
        self.source("Tag1/exportiert/keep-looking-like-source.jpg")
        self.source("OUTPUT/old.jpg")
        self.source("tmp/temporary.jpg")
        self.source("Tag1/moved_freeda_print_2.png")
        self.source("Tag2/.freeda-export-abcd.png")
        folders = []
        import os
        walk = os.walk
        def watched(*args, **kwargs):
            for entry in walk(*args, **kwargs):
                folders.append(Path(entry[0]))
                yield entry
        with patch("freeda.batch.os.walk", side_effect=watched):
            items = discover_files([self.input], exclude=[output])
        self.assertEqual(len(items), 2)
        self.assertNotIn(output, folders)
        self.assertNotIn(self.input / "OUTPUT", folders)

    def test_custom_output_equal_input_keeps_sources_and_ignores_exports(self):
        self.source("Tag1/old_freeda_web.jpg")
        self.assertEqual(len(discover_files([self.input], exclude=[self.input])), 2)

    def test_output_parent_does_not_hide_explicitly_selected_input(self):
        self.assertEqual(len(discover_files([self.input], exclude=[self.base])), 2)

    def test_overlapping_folder_and_file_inputs_are_deduplicated(self):
        items = discover_files([self.input / "Tag1", self.input, self.input / "Tag1/bild.jpg"])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].relative_path, Path("Tag1/bild.jpg"))

    def test_cancelled_discovery_returns_no_partial_selection(self):
        cancel = Event()
        cancel.set()
        with self.assertRaises(Cancelled):
            discover_files([self.input], cancel=cancel)

    def test_same_stem_extensions_have_stable_distinct_targets(self):
        self.source("Tag1/bild.png")
        items, targets = self.items_targets()
        self.assertEqual(len(set(targets)), 3)
        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"old export")
        self.assertEqual(export_targets(items, self.output, self.input, "web", OutputFormat.JPEG), targets)

    def test_rerun_overwrites_outputs_only_and_does_not_rediscover_them(self):
        output = self.input / "exports"
        items, targets = self.items_targets(output)
        originals = {i.source: i.source.read_bytes() for i in items}
        result = run_batch(items, targets, self.options, cancel=Event())
        self.assertEqual(result.written, targets)
        before = targets[0].read_bytes()
        second = run_batch(*self.items_targets(output), replace(self.options, target_long_edge=280), cancel=Event())
        self.assertEqual(second.written, targets)
        self.assertNotEqual(targets[0].read_bytes(), before)
        self.assertEqual(len(discover_files([self.input], exclude=[output])), 2)
        self.assertEqual({i.source: i.source.read_bytes() for i in items}, originals)

    def test_crops_live_in_concrete_source_folders_and_are_not_inputs(self):
        items, targets = self.items_targets()
        first, second = Crop(.1, .1, .7, .7), Crop(.2, .2, .5, .5)
        for item, crop in zip(items, (first, second)):
            save_crop(item.source, "Web", crop)
            save_crop(item.source, "Print", crop)
            self.assertTrue((item.source.parent / FILENAME).is_file())
            self.assertEqual(load_crops(item.source.parent)[item.source.name]["Web"], crop)
        self.assertFalse((self.output / FILENAME).exists())
        self.assertEqual(len(discover_files([self.input])), 2)
        crops = {i.source.resolve(): c for i, c in zip(items, (first, second))}
        with patch("freeda.batch.render_web", wraps=__import__("freeda.render", fromlist=["render_web"]).render_web) as render:
            result = run_batch(items, targets, self.options, cancel=Event(), crops=crops,
                               choose_crop=lambda *_: self.fail("Unexpected manual crop"))
        self.assertEqual(len(result.written), 2)
        self.assertEqual([call.args[1].crop for call in render.call_args_list], [first, second])

    def test_error_does_not_abort_remaining_files_and_progress_reaches_total(self):
        broken = self.input / "Tag1/broken.jpg"
        broken.write_bytes(b"not an image")
        items, targets = self.items_targets()
        progress = []
        result = run_batch(items, targets, self.options, cancel=Event(),
                           progress=lambda index, total, _: progress.append((index, total)))
        self.assertEqual(len(result.written), 2)
        self.assertEqual(len(result.errors), 1)
        self.assertIn(str(broken), result.errors[0])
        self.assertEqual(progress[-1], (3, 3))

    def test_cancel_after_first_file_preserves_remaining_previous_output(self):
        items, targets = self.items_targets()
        targets[1].parent.mkdir(parents=True)
        targets[1].write_bytes(b"previous valid output")
        cancel = Event()
        def progress(index, total, item):
            if index == 1:
                cancel.set()
        result = run_batch(items, targets, self.options, cancel=cancel, progress=progress)
        self.assertTrue(result.cancelled)
        self.assertEqual(result.written, targets[:1])
        self.assertEqual(result.completed, 1)
        self.assertEqual(targets[1].read_bytes(), b"previous valid output")

    def test_cancel_during_atomic_save_keeps_previous_target_and_removes_temporary(self):
        source = self.input / "Tag1/bild.jpg"
        target = self.output / "stereo.jpg"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"previous valid output")
        cancel = Event()
        def metadata(*args, **kwargs):
            cancel.set()
            return MetadataCopyResult(True)
        with patch("freeda.metadata.copy_metadata", side_effect=metadata):
            with self.assertRaises(Cancelled):
                save_render(Image.new("RGB", (20, 10)), target, OutputFormat.JPEG,
                            metadata_source=source, cancel=cancel)
        self.assertEqual(target.read_bytes(), b"previous valid output")
        self.assertEqual(list(target.parent.glob(".freeda-export-*")), [])

    def test_print_crop_pause_reuse_skip_and_cancel(self):
        options = PrintRenderOptions(width_mm=60, height_mm=40, dpi=72)
        items, targets = self.items_targets(options=options)
        crop = Crop(.1, .1, .8, .8)
        calls = []
        def choose(item, image, current, index, total):
            self.assertFalse(targets[index - 1].exists())
            calls.append(item.source)
            return "accept", crop
        result = run_batch(items, targets, options, cancel=Event(), reuse=True, choose_crop=choose)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(result.written), 2)
        result = run_batch(items, targets, options, cancel=Event(), review=True,
                           choose_crop=lambda *_: ("skip", None))
        self.assertEqual(result.skipped, 2)
        self.assertEqual(result.written, [])
        result = run_batch(items, targets, options, cancel=Event(), review=True,
                           choose_crop=lambda *_: ("cancel", None))
        self.assertTrue(result.cancelled)
        self.assertEqual(result.completed, 0)

    def test_original_destination_is_rejected_before_any_processing(self):
        items, _ = self.items_targets()
        with self.assertRaises(ValueError):
            run_batch(items, [items[1].source, self.output / "other.jpg"], self.options, cancel=Event())

    def test_metadata_process_is_cancelled_without_waiting_for_timeout(self):
        source = self.input / "Tag1/bild.jpg"
        target = self.base / "target.jpg"
        target.write_bytes(source.read_bytes())
        cancel = Event()
        launched = []
        spawn = subprocess.Popen
        def slow_tool(arguments, **kwargs):
            process = spawn([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
            launched.append(process)
            return process
        timer = Timer(.2, cancel.set)
        started = time.monotonic()
        timer.start()
        try:
            with patch("freeda.metadata.find_exiftool_path", return_value=Path(sys.executable)), \
                 patch("freeda.metadata.subprocess.Popen", side_effect=slow_tool):
                with self.assertRaises(Cancelled):
                    copy_metadata(source, target, (120, 40), cancel=cancel)
        finally:
            timer.cancel()
            timer.join()
        self.assertTrue(launched and launched[0].poll() is not None)
        self.assertLess(time.monotonic() - started, 3)


if __name__ == "__main__":
    unittest.main()
