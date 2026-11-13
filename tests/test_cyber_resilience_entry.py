"""The cyber resilience entry extends, rather than replaces, the homepage."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ID = "cyber-resilience-log"

class CyberResilienceEntryTests(unittest.TestCase):
    def test_catalogue_metadata_fallback_remain_aligned(self):
        catalogue = json.loads((ROOT / "data/homepage.json").read_text(encoding="utf-8"))
        metadata = json.loads((ROOT / "data/entity-types.json").read_text(encoding="utf-8"))
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        by_id = {entity["id"]: entity for entity in catalogue["entities"]}
        self.assertEqual(len(by_id), len(catalogue["entities"]))
        self.assertGreaterEqual(len(by_id), 28)
        self.assertEqual(set(by_id), set(metadata["records"]))
        self.assertEqual(catalogue["view"]["items"][-1], {"entity_id": ID, "open": False})
        self.assertEqual([item["entity_id"] for item in catalogue["view"]["items"][:9]],
                         ["solar-design-studio","kuiper","gridatlas","ventus-grid-engine",
                          "pipeline-news","identity-registry","electricity-market-intelligence",
                          "metals-cable-prices","cable-engineering"])
        entity = by_id[ID]
        self.assertEqual(entity["operative_release_id"], "20261113")
        self.assertEqual(entity["releases"][0]["url"], "https://ventusltd.github.io/cyber-resilience/")
        self.assertEqual(html.count('<details id="cyber-resilience-log">'), 1)
        self.assertIn('Cyber Resilience Log<small>', html)
        self.assertIn('id="catalogueArchive"', html)
        self.assertIn("Privacy", html)
        self.assertIn("Kuiper", html)

if __name__ == "__main__":
    unittest.main()
