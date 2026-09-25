"""Refresh only homepage ticker from a bounded, explicitly described GitHub sample.

Config is JSON-compatible YAML (stdlib only). GitHub metadata is authoritative for
Pages and commit activity; HTTPS GET proves current route availability. No repo
clones and no third-party credentials. On network/error, the prior feed survives.
Use --offline-validation in browser/CI checks without live API requests.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]


def stamp(now):
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def app_url(url):
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or parsed.username or parsed.password or not host:
        raise ValueError("App destinations must use public HTTPS URLs")
    if host in {"github.com", "www.github.com", "api.github.com", "raw.githubusercontent.com", "gitlab.com", "www.gitlab.com", "bitbucket.org", "www.bitbucket.org", "codeberg.org", "localhost"} or host.endswith(".githubusercontent.com"):
        raise ValueError("Repository, API and raw-content URLs are not app pages")
    if parsed.port not in (None, 443) or re.fullmatch(r"[\d.]+", host) or host.endswith(".local"):
        raise ValueError("Non-public app destination")
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        app_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def verify_page(url, max_bytes):
    url = app_url(url)
    request = Request(url, headers={"User-Agent": "GlobalGrid2050-homepage-ticker/1.0"})
    try:
        with build_opener(SafeRedirect()).open(request, timeout=25) as response:
            if response.status != 200:
                raise ValueError("App route did not return HTTP 200")
            final = app_url(response.geturl())
            if response.headers.get_content_type() != "text/html":
                raise ValueError("App route is not HTML")
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes or b"<html" not in data.lower():
                raise ValueError("App HTML is absent or exceeds configured bound")
            return final
    except HTTPError as error:
        if error.code in {404, 410}:
            return None
        raise RuntimeError(f"App route HTTP failure ({error.code}); prior feed preserved") from None


class GitHub:
    def __init__(self):
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=False)
            if result.returncode:
                raise RuntimeError("GitHub authentication unavailable; prior feed preserved")
            token = result.stdout.strip()
        self.token = token

    def get(self, path, missing_ok=False):
        request = Request("https://api.github.com/" + path, headers={
            "Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "GlobalGrid2050-homepage-ticker/1.0"})
        try:
            # No token in URLs, logs or external live-page requests.
            with build_opener().open(request, timeout=25) as response:
                data = response.read(8000001)
                if len(data) > 8000000:
                    raise ValueError("GitHub response exceeds bound")
                return json.loads(data)
        except HTTPError as error:
            if error.code == 404 and missing_ok:
                return None
            raise RuntimeError(f"GitHub HTTP failure ({error.code}); prior feed preserved") from None


def activity(commits, config, since):
    qualifying = []
    for item in commits:
        commit = item["commit"]
        date = commit["committer"]["date"]
        if datetime.fromisoformat(date.replace("Z", "+00:00")) < since:
            continue
        message = commit["message"].splitlines()[0].lower()
        if any(message.startswith(prefix.lower()) for prefix in config["exclude_commit_prefixes"]):
            continue
        qualifying.append(date)
    return len(qualifying), max(qualifying, default=None), len(commits) >= config["commits_per_repository"]


def create_ticker(config, api, probe=verify_page, now=None):
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=config["window_days"])
    owner = config["owner"]
    if not re.fullmatch(r"[A-Za-z0-9-]+", owner):
        raise ValueError("Invalid GitHub owner")
    listing = api.get(f"users/{owner}/repos?" + urlencode({"per_page": min(config["repository_listing_limit"], 100), "sort": "pushed", "direction": "desc"}))
    listing = [item for item in listing if not item.get("private")]
    repositories = {item["name"]: item for item in listing}
    candidates = list(config["candidates"])
    configured_repos = {item["repository"] for item in candidates}
    for repo in listing:
        if repo.get("has_pages") and not repo.get("archived") and repo["name"] not in configured_repos and repo["name"] not in config["exclude_repositories"] and not any(repo["name"].startswith(prefix) for prefix in config.get("exclude_repository_prefixes", [])):
            candidates.append({"repository": repo["name"], "label": repo["name"].replace("-", " ").title()})
    candidates = candidates[:min(config["max_candidates"], 20)]
    cache, items, skipped, seen, checks = {}, [], [], set(), []
    for candidate in candidates:
        name = candidate["repository"]
        if name not in repositories or not repositories[name].get("has_pages"):
            skipped.append({"repository": name, "reason": "not_in_bounded_listing_or_no_pages"})
            continue
        if name not in cache:
            pages = api.get(f"repos/{owner}/{name}/pages", missing_ok=True)
            if not pages or pages.get("status") not in {"built", None} or not pages.get("html_url"):
                cache[name] = None
            else:
                query = urlencode({"since": stamp(since), "until": stamp(now), "per_page": min(config["commits_per_repository"], 100)})
                commits = api.get(f"repos/{owner}/{name}/commits?{query}")
                cache[name] = (pages, activity(commits, config, since))
        if cache[name] is None:
            skipped.append({"repository": name, "reason": "pages_missing_or_not_built"})
            continue
        pages, (count, latest, capped) = cache[name]
        if count == 0:
            skipped.append({"repository": name, "reason": "no_qualifying_commits_in_window"})
            continue
        url = candidate.get("url", pages["html_url"])
        final = probe(url, config["max_html_bytes"])
        if final is None:
            skipped.append({"repository": name, "reason": "live_route_missing"})
            continue
        final = app_url(final)
        if final in seen:
            skipped.append({"repository": name, "reason": "duplicate_final_url"})
            continue
        seen.add(final)
        checks.append({"repository": f"{owner}/{name}", "url": final, "status": "verified_https_html_200", "activity_count": count, "activity_capped": capped})
        items.append({"label": candidate["label"], "url": final, "repository": f"{owner}/{name}",
                      "activity_count": count, "activity_capped": capped, "last_activity": latest,
                      "verified_at": stamp(now), "pages_status": pages.get("status") or "not_reported",
                      "verification": "Pages API configured; final HTTPS HTML HTTP 200"})
    items.sort(key=lambda item: (item["activity_count"], item["last_activity"], item["label"]), reverse=True)
    if not items:
        raise ValueError("No verified active app pages; prior feed preserved")
    return {"schema_version": 1, "items": items[:min(config["max_items"], 12)], "updated_at": stamp(now), "window_days": config["window_days"],
            "method": {"description": config["method_note"], "grain": "one verified final app URL", "key": "url",
                       "repository_sample_size": len(listing), "routes_considered": len(candidates),
                       "commits_per_repository_cap": config["commits_per_repository"], "checks": checks, "skipped": skipped}}


def validate_ticker(ticker):
    if not 0 < len(ticker["items"]) <= 12 or ticker["window_days"] != 30:
        raise ValueError("Invalid ticker bounds")
    urls = [app_url(item["url"]) for item in ticker["items"]]
    if len(urls) != len(set(urls)):
        raise ValueError("Duplicate app URLs")
    for item in ticker["items"]:
        if not item["label"] or not isinstance(item["activity_count"], int) or not 0 < item["activity_count"] <= 100:
            raise ValueError("Invalid ticker activity")
        if not isinstance(item["activity_capped"], bool) or not item["last_activity"]:
            raise ValueError("Missing activity provenance")


def refresh(config, output, api=None, probe=verify_page):
    # Finish ALL network work before altering the last good feed.
    ticker = create_ticker(config, api or GitHub(), probe)
    validate_ticker(ticker)
    encoded = json.dumps(ticker, indent=2, ensure_ascii=False) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.with_suffix(".json.tmp")
    try:
        staging.write_text(encoded, encoding="utf-8", newline="\n")
        validate_ticker(json.loads(staging.read_text(encoding="utf-8")))
        staging.replace(output)
    finally:
        if staging.exists():
            staging.unlink()
    return ticker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/active-pages.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "data/active-pages.json")
    parser.add_argument("--offline-validation", "--check", dest="offline_validation", action="store_true")
    args = parser.parse_args()
    if args.offline_validation:
        validate_ticker(json.loads(args.output.read_text(encoding="utf-8")))
        print("Offline ticker schema/key checks passed; live availability is not rechecked")
    else:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        ticker = refresh(config, args.output)
        print(f"Verified {len(ticker['items'])} live app pages; {ticker['method']['routes_considered']} candidate routes checked")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Never print request headers, token, subprocess stdout or traceback locals.
        print(f"Refresh failed; prior feed preserved: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(1)
