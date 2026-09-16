import json
import tempfile
import unittest
from pathlib import Path

from core import DEFAULTS, clamp_position, read_settings, write_settings


class SettingsTests(unittest.TestCase):
    def test_offscreen_and_negative_monitor_coordinates(self):
        self.assertEqual(clamp_position(-3000, 4000, 300, 370, (-1920, 0, 0, 1080)), (-1920, 710))
        self.assertEqual(clamp_position(10, -40, 300, 370, (0, 0, 200, 200)), (0, 0))

    def test_corrupt_and_wrong_type_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "settings.json"
            for content in ("{", "[]", "null"):
                p.write_text(content)
                self.assertEqual(read_settings(p), DEFAULTS)
            p.write_text(json.dumps({"scale": 9, "wander": "false", "position": [True, 0]}))
            self.assertEqual(read_settings(p)["scale"], 1.6)
            self.assertTrue(read_settings(p)["wander"])
            self.assertNotIn("position", read_settings(p))

    def test_profile_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "profile" / "settings.json"
            data = dict(DEFAULTS, scale=.75, wander=False, position=[-500, 300])
            write_settings(p, data)
            self.assertEqual(read_settings(p), data)


if __name__ == "__main__":
    unittest.main()
