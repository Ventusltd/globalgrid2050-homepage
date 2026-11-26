import json
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class VedicEntryTests(unittest.TestCase):
    def test_vedic_section(self):
        d = json.loads((ROOT/"data/homepage.json").read_text())
        m = json.loads((ROOT/"data/entity-types.json").read_text())
        h = (ROOT/"index.html").read_text()
        e = [e for e in d["entities"] if e["id"] == "vedic"]
        self.assertEqual(len(e),1)
        self.assertEqual(d["view"]["items"][10], {"entity_id":"vedic","open":False})
        self.assertEqual(e[0]["operative_release_id"],"v1")
        self.assertEqual(e[0]["releases"][0]["url"],"https://ventusltd.github.io/vedic-/")
        self.assertEqual(m["records"]["vedic"]["type"],"catalogue")
        self.assertEqual(h.count('<details id="vedic">'),1)
        self.assertIn('href="https://ventusltd.github.io/vedic-/">Open VEDIC',h)
        self.assertIn('id="satnav-concept"',h)
