import unittest

from freeda.window import window_sizes


class WindowTests(unittest.TestCase):
    def test_taskbar_and_150_percent_scaling_reduce_minimum_height(self):
        initial, minimum = window_sizes(1920, 1008, 1.5, (1400, 860), (1120, 720))
        self.assertLess(initial[1], 672)
        self.assertLess(minimum[1], 672)
        self.assertLess(initial[0], 1280)
        self.assertLessEqual(minimum[0], initial[0])

    def test_large_monitor_keeps_preferred_dimensions(self):
        self.assertEqual(window_sizes(2560, 1400, 1, (1400, 860), (1120, 720)),
                         ((1400, 860), (1120, 720)))

    def test_small_crop_dialog_fits_in_scaled_work_area(self):
        initial, minimum = window_sizes(1366, 720, 1.25, (1080, 760), (900, 650))
        self.assertLess(initial[1] * 1.25, 720)
        self.assertLess(minimum[1] * 1.25, 720)
        self.assertLess(initial[0] * 1.25, 1366)


if __name__ == "__main__":
    unittest.main()
