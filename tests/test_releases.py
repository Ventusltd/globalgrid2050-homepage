"""Contract and transition tests; fixtures never modify the real catalogue."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "releases.py"
SPEC = importlib.util.spec_from_file_location("releases", SCRIPT)
releases = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(releases)


def fixture():
    return {
        "schema_version": 1,
        "entities": [{
            "id": "tool", "title": "Tool", "subtitle": "Engineering",
            "description": "Example tool", "launch_label": "Open tool",
            "operative_release_id": "A",
            "releases": [{
                "id": rid, "label": f"Release {rid}",
                "url": f"https://example.com/releases/{rid}/",
                "published_at": "2026-09-25", "status": status,
                "source_ref": f"owner/repo@{rid}",
            } for rid, status in (("A", "available"), ("B", "available"), ("C", "candidate"))],
        }],
        "view": {"items": [{"entity_id": "tool", "open": True}], "archive_url": "https://example.com/archive/"},
    }


class ReleaseContractTests(unittest.TestCase):
    def test_promotion_and_rollback_preserve_every_release(self):
        original = fixture()
        expected_releases = copy.deepcopy(original["entities"][0]["releases"])
        promoted = releases.promote(original, "tool", "B", "Target release tested")
        self.assertEqual(promoted["entities"][0]["operative_release_id"], "B")
        self.assertEqual(original["entities"][0]["operative_release_id"], "A")
        self.assertEqual(promoted["entities"][0]["releases"], expected_releases)
        archived = [r for r in promoted["entities"][0]["releases"] if r["status"] == "available" and r["id"] != "B"]
        self.assertEqual([r["url"] for r in archived], ["https://example.com/releases/A/"])
        rolled_back = releases.promote(promoted, "tool", "A", "Regression rollback")
        self.assertEqual(rolled_back["entities"][0]["operative_release_id"], "A")
        self.assertEqual(rolled_back["entities"][0]["releases"], expected_releases)
        self.assertEqual([(p["from_release_id"], p["to_release_id"]) for p in rolled_back["promotions"]], [("A", "B"), ("B", "A")])
        self.assertTrue(all(p["promoted_at"].endswith("Z") for p in rolled_back["promotions"]))

    def test_candidate_and_repeated_promotion_refused(self):
        for target in ("C", "A", "missing"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                releases.promote(fixture(), "tool", target, "Testing refusal")
        with self.assertRaises(ValueError):
            releases.promote(fixture(), "tool", "B", " ")

    def test_invalid_references_and_duplicates(self):
        mutations = [
            lambda d: d["entities"].append(copy.deepcopy(d["entities"][0])),
            lambda d: d["entities"][0]["releases"].append(copy.deepcopy(d["entities"][0]["releases"][0])),
            lambda d: d["entities"][0].update(operative_release_id="missing"),
            lambda d: d["entities"][0].update(operative_release_id="C"),
            lambda d: d["entities"][0].update(parent_id="missing"),
            lambda d: d["entities"][0].update(parent_id="tool"),
            lambda d: d["view"]["items"][0].update(entity_id="missing"),
            lambda d: d["view"]["items"].append(copy.deepcopy(d["view"]["items"][0])),
            lambda d: d["view"]["items"][0].update(open="true"),
            lambda d: d.update(schema_version=True),
            lambda d: d["entities"][0]["releases"][0].update(source_ref=" "),
            lambda d: d["entities"][0]["releases"][0].update(published_at="2026-02-30"),
            lambda d: d["entities"][0]["releases"][0].update(published_at="2026-09-25T12:00:00"),
            lambda d: d.update(unexpected="schema drift"),
        ]
        for i, mutation in enumerate(mutations):
            data = fixture()
            mutation(data)
            with self.subTest(case=i), self.assertRaises(ValueError):
                releases.validate(data)

    def test_parent_chain_and_cycle(self):
        data = fixture()
        child = copy.deepcopy(data["entities"][0])
        child.update(id="variant", parent_id="tool")
        data["entities"].append(child)
        releases.validate(data)
        data["entities"][0]["parent_id"] = "variant"
        with self.assertRaisesRegex(ValueError, "cycle"):
            releases.validate(data)

    def test_dangerous_urls(self):
        for url in ("javascript:alert(1)", "data:text/html,test", "http://example.com", "//example.com", "https://user:secret@example.com", "https://example.com\\@evil.com", "https://example.com/\npath", "https://", "https://example.com:bad", "https://example.com:99999", "https://%65xample.com"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                data = fixture()
                data["entities"][0]["releases"][0]["url"] = url
                releases.validate(data)

    def test_archive_manifest_and_development(self):
        data = fixture()
        data["entities"][0]["releases"][0]["published_at"] = None
        data["entities"][0]["releases"][0].update(archive_url="https://example.com/commit/abc/manifest.json", archive_kind="manifest")
        data["development"] = [{"entity_id": "tool", "label": "Tool development", "status": "In development", "url": "https://example.com/repo/", "description": "A compact development highlight.", "evidence_summary": "Synthetic fixture tested."}]
        releases.validate(data)
        promoted = releases.promote(data, "tool", "B", "Verified")
        self.assertEqual(promoted["entities"][0]["releases"][0]["archive_kind"], "manifest")
        for key, value in (("entity_id", "missing"), ("status", "available"), ("url", "javascript:evil"), ("description", " "), ("evidence_summary", 12)):
            invalid = copy.deepcopy(data)
            invalid["development"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                releases.validate(invalid)
        del data["entities"][0]["releases"][0]["archive_url"]
        with self.assertRaises(ValueError):
            releases.validate(data)

    def test_catalogue_growth_has_no_fixed_entity_count(self):
        data = fixture()
        for number in range(8):
            extra = copy.deepcopy(data["entities"][0])
            extra["id"] = f"extra-{number}"
            data["entities"].append(extra)
            data["view"]["items"].append({"entity_id": extra["id"], "open": False})
        releases.validate(data)
        self.assertEqual(len(data["entities"]), 9)

    def test_audit_drift_rejected(self):
        data = releases.promote(fixture(), "tool", "B", "Verified")
        data["entities"][0]["operative_release_id"] = "A"
        with self.assertRaisesRegex(ValueError, "promotion history"):
            releases.validate(data)

    def test_cli_writes_then_reads_back_and_refusal_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "homepage.json"
            path.write_text(json.dumps(fixture()), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "--file", str(path), "promote", "tool", "B", "--reason", "Verified target"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = releases.load(path)
            self.assertEqual(data["entities"][0]["operative_release_id"], "B")
            before = path.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT), "promote", "tool", "B", "--reason", "Repeat", "--file", str(path)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(path.read_bytes(), before)
            result = subprocess.run([sys.executable, str(SCRIPT), "validate", "--file", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_duplicate_json_property_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"schema_version": 1, "schema_version": 1}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON property"):
                releases.load(path)


if __name__ == "__main__":
    unittest.main()
