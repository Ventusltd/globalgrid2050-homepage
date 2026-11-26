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
        releases = {r["id"]: r for r in e[0]["releases"]}
        self.assertEqual(len(releases), len(e[0]["releases"]))
        self.assertEqual(releases["v1"]["url"],"https://ventusltd.github.io/vedic-/")
        self.assertEqual(releases["v1"]["archive_url"],"https://ventusltd.github.io/vedic-/releases/202611260135-v1/")
        self.assertEqual(releases["v1"]["archive_kind"],"app")
        v2 = releases["202611261351"]
        self.assertEqual(v2["url"],"https://ventusltd.github.io/vedic-/releases/202611261351/")
        self.assertEqual(v2["source_ref"],"https://github.com/Ventusltd/vedic-/tree/55ff568b378acff4adae02fb5c758b4f4f8c6bcd")
        self.assertEqual(v2["status"],"available")
        promotions = [p for p in d["promotions"] if p["entity_id"] == "vedic"]
        self.assertEqual((promotions[0]["from_release_id"], promotions[0]["to_release_id"]),("v1","202611261351"))
        self.assertEqual(promotions[-1]["to_release_id"],e[0]["operative_release_id"])
        operative = releases[e[0]["operative_release_id"]]
        self.assertEqual(operative["status"],"available")
        self.assertEqual(m["records"]["vedic"]["type"],"catalogue")
        self.assertEqual(h.count('<details id="vedic">'),1)
        self.assertIn(f'href="{operative["url"]}">Open VEDIC',h)
        self.assertIn('id="satnav-concept"',h)
