from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("active_pages", ROOT / "scripts/fetch_active_pages.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeAPI:
    def get(self, path, missing_ok=False):
        if path.startswith("users/"):
            return [{"name": "one", "has_pages": True}]
        if path.endswith("/pages"):
            return {"html_url": "https://example.org/app/", "status": "built"}
        return [{"commit": {"message": "real work", "committer": {"date": "2026-09-24T00:00:00Z"}}}]


class ActivePageTests(unittest.TestCase):
    def config(self):
        config = json.loads((ROOT / "config/active-pages.yaml").read_text())
        config["candidates"] = [{"repository": "one", "label": "One"}, {"repository": "one", "label": "Duplicate"}]
        return config

    def test_rejects_repo_raw_and_insecure_destinations(self):
        for url in ["https://github.com/a/b", "https://gitlab.com/a/b", "https://bitbucket.org/a/b", "https://raw.githubusercontent.com/a/b", "http://example.org", "https://api.github.com/repos/a/b", "https://user:pass@example.org"]:
            with self.assertRaises(ValueError):
                module.app_url(url)
        self.assertEqual(module.app_url("https://ventusltd.github.io/sld/"), "https://ventusltd.github.io/sld/")

    def test_deduplicates_live_routes(self):
        ticker = module.create_ticker(self.config(), FakeAPI(), lambda url, limit: url, datetime(2026, 9, 25, tzinfo=timezone.utc))
        self.assertEqual(len(ticker["items"]), 1)
        self.assertEqual(ticker["items"][0]["activity_count"], 1)
        self.assertEqual(ticker["method"]["skipped"][0]["reason"], "duplicate_final_url")

    def test_activity_excludes_self_refresh_and_marks_cap(self):
        config = self.config()
        config["commits_per_repository"] = 2
        commits = [{"commit": {"message": title, "committer": {"date": "2026-09-24T00:00:00Z"}}} for title in ["real change", "chore: refresh active pages"]]
        count, date, capped = module.activity(commits, config, datetime(2026, 9, 1, tzinfo=timezone.utc))
        self.assertEqual(count, 1)
        self.assertTrue(capped)

    def test_network_failure_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "homepage.json"
            previous = b'{"entities": [], "ticker": {"old": true}}'
            path.write_bytes(previous)
            def fail(url, limit):
                raise OSError("network failure")
            with self.assertRaises(OSError):
                module.refresh(self.config(), path, FakeAPI(), fail)
            self.assertEqual(path.read_bytes(), previous)

    def test_private_repository_cannot_enter_public_feed(self):
        class PrivateAPI(FakeAPI):
            def get(self, path, missing_ok=False):
                if path.startswith("users/"):
                    return [{"name": "one", "has_pages": True, "private": True}]
                raise AssertionError("Private repository must not be probed")
        with self.assertRaises(ValueError):
            module.create_ticker(self.config(), PrivateAPI(), lambda url, limit: url, datetime(2026, 9, 25, tzinfo=timezone.utc))

    def test_missing_pages_is_explicitly_skipped(self):
        class MissingAPI(FakeAPI):
            def get(self, path, missing_ok=False):
                if path.endswith("/pages"):
                    return None
                return super().get(path, missing_ok)
        with self.assertRaisesRegex(ValueError, "No verified"):
            module.create_ticker(self.config(), MissingAPI(), lambda url, limit: url, datetime(2026, 9, 25, tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
