import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from freeda.resources import portable_settings_path


class PortableSettingsTests(unittest.TestCase):
    def test_frozen_settings_are_next_to_executable_not_internal_resources(self):
        executable = str(Path("portable/Freeda.exe").resolve())
        with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", executable), \
                patch.object(sys, "_MEIPASS", "elsewhere/_internal", create=True):
            self.assertEqual(portable_settings_path(), Path(executable).parent / "settings.json")

    def test_macos_settings_are_beside_app_bundle(self):
        executable=str(Path("portable/Freeda.app/Contents/MacOS/Freeda").resolve())
        with patch.object(sys,"frozen",True,create=True), patch.object(sys,"executable",executable), patch.object(sys,"platform","darwin"):
            self.assertEqual(portable_settings_path(),Path(executable).parents[3]/"settings.json")

    def test_source_settings_are_in_project_directory(self):
        with patch.object(sys, "frozen", False, create=True):
            self.assertEqual(portable_settings_path(), Path(__file__).resolve().parents[1] / "settings.json")


if __name__ == "__main__":
    unittest.main()
