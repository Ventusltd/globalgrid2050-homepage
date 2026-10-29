import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("release_gridatlas", ROOT / "scripts/release_gridatlas.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GridAtlasReleaseTests(unittest.TestCase):
    def setUp(self):
        self.data = module.releases.load(ROOT / "data/homepage.json")

    def test_label_format(self):
        self.assertEqual(module.label("v9.172", "2026-10-28T18:53:00Z"), "V9.172 - 28 October 2026")
        self.assertEqual(module.label("v9.156", "2026-09-24T13:34:00Z"), "V9.156 - 24 September 2026")

    def test_next_release_is_promoted_and_history_retained(self):
        before = next(e for e in self.data["entities"] if e["id"] == "gridatlas")
        release = module.build_release("209912311200", "v9.999", "2099-12-31T12:00:00Z", "https://github.com/Ventusltd/gridatlas/commit/" + "0" * 40,
                                       ("https://ventusltd.github.io/gridatlas/atlas/v/209912311200/", "app"))
        result = module.apply(copy.deepcopy(self.data), release, "test promotion")
        after = next(e for e in result["entities"] if e["id"] == "gridatlas")
        self.assertEqual(after["operative_release_id"], "209912311200")
        self.assertEqual(after["releases"][:-1], before["releases"])
        self.assertEqual(after["description"], before["description"])
        self.assertEqual(result["promotions"][-1]["from_release_id"], before["operative_release_id"])

    def test_duplicate_release_refused(self):
        operative = next(e for e in self.data["entities"] if e["id"] == "gridatlas")["operative_release_id"]
        release = module.build_release(operative, "v1.0", "2026-01-01T00:00:00Z", "https://example.org/x", None)
        with self.assertRaises(ValueError):
            module.apply(copy.deepcopy(self.data), release, "repeat")


if __name__ == "__main__":
    unittest.main()
