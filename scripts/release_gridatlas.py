"""One-command GridAtlas homepage release, plus the domain pin for globalgrid2050.

Run from the repository root:

    python scripts/release_gridatlas.py release 202610281340 v9.172 \
        --published-at 2026-10-28T18:53:00Z \
        --description "Find sites ... Now with ..."      # optional

    python scripts/release_gridatlas.py pin [COMMIT]     # after the release PR merges

`release` reads the live GridAtlas pointer (atlas/current.json on gridatlas main)
and refuses unless its generation and composition_version match the arguments,
so the homepage can only advertise what the canonical route already serves. It
then appends one available release (label "V9.172 - 28 October 2026"), promotes
it with scripts/releases.py (keeping every earlier release and adding an audit
entry), and rebuilds the no-JavaScript fallback in index.html.

Availability is the owner's acceptance of that GridAtlas release, asserted by
whoever runs this command; this script does not test the app.

`pin` prints catalogue/homepage-owner.json for globalgrid2050: the commit plus
SHA-256 of the seven bundle files at that commit (read with `git show`).
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import releases  # noqa: E402

ENTITY = "gridatlas"
REPO = "Ventusltd/gridatlas"
LIVE_ROUTE = "https://ventusltd.github.io/gridatlas/atlas/"
PINNED_ROUTE = LIVE_ROUTE + "v/{generation}/"
MANIFEST = LIVE_ROUTE + "manifests/{generation}-composition.json"
CURRENT_RAW = f"https://raw.githubusercontent.com/{REPO}/main/atlas/current.json"
BUNDLE = ("index.html", "assets/versioned-homepage.css", "assets/versioned-homepage.js",
          "data/homepage.json", "data/active-pages.json", "data/presentation.json", "data/entity-types.json")


def fetch(url, limit=5_000_000):
    request = urllib.request.Request(url, headers={"User-Agent": "globalgrid2050-homepage-release"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read(limit)


def exists(url):
    try:
        fetch(url, 1)
        return True
    except OSError:
        return False


def label(version, published_at):
    when = datetime.fromisoformat(published_at.replace("Z", "+00:00")).astimezone(timezone.utc)
    return f"{version.upper()} - {when.day} {when:%B %Y}"


def build_release(generation, version, published_at, source_ref, archive):
    release = {"id": generation, "label": label(version, published_at), "url": LIVE_ROUTE,
               "published_at": published_at, "status": "available", "source_ref": source_ref}
    if archive:
        release["archive_url"], release["archive_kind"] = archive
    return release


def apply(data, release, reason, description=None):
    entity = next(e for e in data["entities"] if e["id"] == ENTITY)
    releases.require(all(r["id"] != release["id"] for r in entity["releases"]), f"release {release['id']} already recorded")
    entity["releases"].append(release)
    if description:
        entity["description"] = description.strip()
    return releases.promote(data, ENTITY, release["id"], reason)


def release_command(args):
    releases.require(re.fullmatch(r"\d{12}", args.generation) is not None, "generation must be 12 digits (YYYYMMDDhhmm)")
    releases.require(re.fullmatch(r"v\d+(\.\d+)+", args.version) is not None, "version must look like v9.172")
    releases.iso_date(args.published_at, "--published-at", utc_only=True)
    source_ref, archive = args.source_ref, None
    if not args.offline:
        current = json.loads(fetch(CURRENT_RAW))
        releases.require(current.get("generation") == args.generation,
                         f"live pointer serves {current.get('generation')}, not {args.generation}; release GridAtlas first")
        releases.require(current.get("composition_version") == args.version,
                         f"live pointer composition_version is {current.get('composition_version')}, not {args.version}")
        if not source_ref:
            commits = json.loads(fetch(f"https://api.github.com/repos/{REPO}/commits?path=atlas/current.json&per_page=1"))
            source_ref = f"https://github.com/{REPO}/commit/{commits[0]['sha']}"
        raw = f"https://raw.githubusercontent.com/{REPO}/main/atlas/"
        if exists(raw + f"v/{args.generation}/index.html"):
            archive = (PINNED_ROUTE.format(generation=args.generation), "app")
        elif exists(raw + f"manifests/{args.generation}-composition.json"):
            archive = (MANIFEST.format(generation=args.generation), "manifest")
    releases.require(bool(source_ref), "--source-ref is required with --offline")
    if args.archive_url:
        archive = (args.archive_url, args.archive_kind)
    data = releases.load(args.file)
    release = build_release(args.generation, args.version, args.published_at, source_ref, archive)
    reason = args.reason or f"GridAtlas {args.version} (generation {args.generation}) is live on the canonical route and accepted by the owner"
    data = apply(data, release, reason, args.description)
    releases.write_validated(args.file, data)
    subprocess.run([sys.executable, str(ROOT / "scripts/build_homepage_fallback.py")], check=True, cwd=ROOT)
    print(f"Promoted {ENTITY} to {release['id']} ({release['label']}); earlier releases retained.")
    print("Next: run the checks in docs/GRIDATLAS-RELEASE.md, open a PR, merge, then `python scripts/release_gridatlas.py pin`.")
    return 0


def pin_command(args):
    commit = subprocess.run(["git", "rev-parse", args.commit], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    files = {}
    for name in BUNDLE:
        blob = subprocess.run(["git", "show", f"{commit}:{name}"], cwd=ROOT, check=True, capture_output=True).stdout
        files[name] = hashlib.sha256(blob).hexdigest()
    print(json.dumps({"repository": "Ventusltd/globalgrid2050-homepage", "commit": commit, "files": files}, indent=2))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    rel = commands.add_parser("release", help="Record and promote a live GridAtlas generation")
    rel.add_argument("generation")
    rel.add_argument("version")
    rel.add_argument("--published-at", required=True, help="UTC time the generation went live, e.g. 2026-10-28T18:53:00Z")
    rel.add_argument("--description", help="Replace the GridAtlas description shown in its nest")
    rel.add_argument("--reason", help="Promotion audit reason")
    rel.add_argument("--source-ref", help="Default: the gridatlas commit that last changed atlas/current.json")
    rel.add_argument("--archive-url", help="Default: atlas/v/GENERATION/ if published, else its composition manifest")
    rel.add_argument("--archive-kind", choices=("app", "manifest"), default="app")
    rel.add_argument("--offline", action="store_true", help="Skip live-pointer checks (requires --source-ref)")
    rel.add_argument("--file", type=Path, default=releases.DEFAULT_FILE)
    pin = commands.add_parser("pin", help="Print catalogue/homepage-owner.json for globalgrid2050")
    pin.add_argument("commit", nargs="?", default="origin/main")
    args = parser.parse_args(argv)
    try:
        return release_command(args) if args.command == "release" else pin_command(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
