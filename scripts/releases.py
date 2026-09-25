"""Validate homepage release metadata and explicitly promote an available release.

Run from the repository root:
    python scripts/releases.py validate
    python scripts/releases.py promote ENTITY RELEASE --reason "Reviewed and tested"

The catalogue grain is one entity per id, one release per (entity id, release id).
An available non-operative release is archived implicitly, never removed here.
Availability is a maintainer assertion: this tool does not test the linked app.
"""

import argparse
import copy
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit


DEFAULT_FILE = Path(__file__).resolve().parents[1] / "data" / "homepage.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, required, optional, context):
    require(isinstance(value, dict), f"{context}: expected object")
    require(set(required) <= value.keys(), f"{context}: missing fields {set(required) - value.keys()}")
    require(value.keys() <= set(required) | set(optional), f"{context}: unknown fields {value.keys() - set(required) - set(optional)}")


def nonempty(value, context):
    require(isinstance(value, str) and bool(value.strip()), f"{context}: expected nonempty text")


def identifier(value, context):
    nonempty(value, context)
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*", value) is not None, f"{context}: invalid identifier")


def https_url(value, context):
    nonempty(value, context)
    require(not any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value), f"{context}: whitespace/control character in URL")
    require("\\" not in value, f"{context}: backslash in URL")
    try:
        parts = urlsplit(value)
        port = parts.port
        require(parts.scheme == "https" and bool(parts.hostname), f"{context}: HTTPS URL required")
        require(parts.username is None and parts.password is None, f"{context}: credentials forbidden")
        require("%" not in parts.netloc, f"{context}: encoded hostname forbidden")
        require(port is None or 0 < port <= 65535, f"{context}: invalid port")
    except ValueError as exc:
        raise ValueError(f"{context}: invalid URL ({exc})") from exc


def iso_date(value, context, utc_only=False):
    nonempty(value, context)
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) and not utc_only:
            date.fromisoformat(value)
        else:
            require("T" in value, f"{context}: ISO date or timezone-aware timestamp required")
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            require(parsed.tzinfo is not None, f"{context}: timestamp needs timezone")
            if utc_only:
                require(parsed.utcoffset().total_seconds() == 0, f"{context}: UTC required")
    except ValueError as exc:
        raise ValueError(f"{context}: invalid date ({exc})") from exc


def validate(data):
    fields(data, {"schema_version", "entities", "view"}, {"promotions", "development"}, "catalogue")
    require(type(data["schema_version"]) is int and data["schema_version"] == 1, "schema_version must be 1")
    require(isinstance(data["entities"], list), "entities must be an array")
    entities = {}
    releases = {}
    for entity in data["entities"]:
        fields(entity, {"id", "title", "subtitle", "description", "launch_label", "operative_release_id", "releases"}, {"parent_id"}, "entity")
        identifier(entity["id"], "entity.id")
        eid = entity["id"]
        require(eid not in entities, f"duplicate entity id: {eid}")
        entities[eid] = entity
        for key in ("title", "subtitle", "description", "launch_label"):
            nonempty(entity[key], f"{eid}.{key}")
        if "parent_id" in entity:
            identifier(entity["parent_id"], f"{eid}.parent_id")
        identifier(entity["operative_release_id"], f"{eid}.operative_release_id")
        require(isinstance(entity["releases"], list) and entity["releases"], f"{eid}: releases must be a nonempty array")
        releases[eid] = {}
        for release in entity["releases"]:
            fields(release, {"id", "label", "url", "published_at", "status", "source_ref"}, {"archive_url", "archive_kind"}, f"{eid}.release")
            identifier(release["id"], f"{eid}.release.id")
            rid = release["id"]
            require(rid not in releases[eid], f"{eid}: duplicate release id {rid}")
            releases[eid][rid] = release
            nonempty(release["label"], f"{eid}/{rid}.label")
            nonempty(release["source_ref"], f"{eid}/{rid}.source_ref")
            https_url(release["url"], f"{eid}/{rid}.url")
            require(("archive_url" in release) == ("archive_kind" in release), f"{eid}/{rid}: archive_url and archive_kind must be supplied together")
            if "archive_url" in release:
                https_url(release["archive_url"], f"{eid}/{rid}.archive_url")
                require(release["archive_kind"] in ("app", "manifest"), f"{eid}/{rid}: invalid archive_kind")
            if release["published_at"] is not None:
                iso_date(release["published_at"], f"{eid}/{rid}.published_at")
            require(release["status"] in ("available", "candidate"), f"{eid}/{rid}: invalid status")
        current = releases[eid].get(entity["operative_release_id"])
        require(current is not None, f"{eid}: operative release reference missing")
        require(current["status"] == "available", f"{eid}: operative release must be available")

    # Iterative traversal supports deep product hierarchies without recursion limits.
    complete = set()
    for eid in entities:
        path = set()
        cursor = eid
        while cursor is not None and cursor not in complete:
            require(cursor in entities, f"{eid}: unknown parent {cursor}")
            require(cursor not in path, f"{eid}: parent cycle")
            path.add(cursor)
            cursor = entities[cursor].get("parent_id")
        complete.update(path)

    view = data["view"]
    fields(view, {"items", "archive_url"}, set(), "view")
    https_url(view["archive_url"], "view.archive_url")
    require(isinstance(view["items"], list), "view.items must be an array")
    seen = set()
    for item in view["items"]:
        fields(item, {"entity_id", "open"}, set(), "view.item")
        identifier(item["entity_id"], "view.item.entity_id")
        eid = item["entity_id"]
        require(eid in entities, f"view: unknown entity {eid}")
        require(eid not in seen, f"view: duplicate entity {eid}")
        require("parent_id" not in entities[eid], f"view: {eid} is not a root entity")
        require(type(item["open"]) is bool, f"view/{eid}.open must be boolean")
        seen.add(eid)

    development = data.get("development", [])
    require(isinstance(development, list), "development must be an array")
    seen_development = set()
    for entry in development:
        fields(entry, {"entity_id", "label", "status", "url"}, {"description", "evidence_summary"}, "development entry")
        identifier(entry["entity_id"], "development.entity_id")
        eid = entry["entity_id"]
        require(eid in entities, f"development: unknown entity {eid}")
        require(eid not in seen_development, f"development: duplicate entity {eid}")
        seen_development.add(eid)
        nonempty(entry["label"], "development.label")
        for key in ("description", "evidence_summary"):
            if key in entry:
                nonempty(entry[key], f"development.{key}")
        require(entry["status"] == "In development", "development.status must be 'In development'")
        https_url(entry["url"], "development.url")

    audit = data.get("promotions", [])
    require(isinstance(audit, list), "promotions must be an array")
    last = {}
    for entry in audit:
        fields(entry, {"entity_id", "from_release_id", "to_release_id", "reason", "promoted_at"}, set(), "promotion")
        identifier(entry["entity_id"], "promotion.entity_id")
        eid = entry["entity_id"]
        require(eid in entities, f"promotion: unknown entity {eid}")
        for key in ("from_release_id", "to_release_id"):
            identifier(entry[key], f"promotion.{key}")
            require(entry[key] in releases[eid], f"promotion: unknown release {eid}/{entry[key]}")
        require(entry["from_release_id"] != entry["to_release_id"], "promotion must change release")
        require(eid not in last or last[eid] == entry["from_release_id"], f"{eid}: broken promotion history")
        nonempty(entry["reason"], "promotion.reason")
        iso_date(entry["promoted_at"], "promotion.promoted_at", utc_only=True)
        last[eid] = entry["to_release_id"]
    for eid, rid in last.items():
        require(entities[eid]["operative_release_id"] == rid, f"{eid}: operative release differs from promotion history")
    return data


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON property: {key}")
        result[key] = value
    return result


def load(path):
    return validate(json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_object))


def promote(data, entity_id, release_id, reason):
    validate(data)
    nonempty(reason, "promotion reason")
    result = copy.deepcopy(data)
    entity = next((e for e in result["entities"] if e["id"] == entity_id), None)
    require(entity is not None, f"unknown entity: {entity_id}")
    target = next((r for r in entity["releases"] if r["id"] == release_id), None)
    require(target is not None, f"unknown release: {entity_id}/{release_id}")
    require(target["status"] == "available", "candidate releases cannot be promoted; verify the release and mark it available first")
    previous = entity["operative_release_id"]
    require(previous != release_id, "release is already operative; no changes made")
    entity["operative_release_id"] = release_id
    result.setdefault("promotions", []).append({
        "entity_id": entity_id,
        "from_release_id": previous,
        "to_release_id": release_id,
        "reason": reason.strip(),
        "promoted_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    })
    return validate(result)


def write_validated(path, data):
    """Read back a staged file before atomically replacing the local configuration."""
    path = Path(path)
    staged = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, prefix=".homepage-", suffix=".json", delete=False) as output:
            staged = Path(output.name)
            json.dump(data, output, indent=2, ensure_ascii=False, allow_nan=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        load(staged)
        os.replace(staged, path)
    finally:
        if staged is not None and staged.exists():
            staged.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    commands = parser.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("validate", help="Validate the local homepage configuration")
    promotion = commands.add_parser("promote", help="Change the operative release and append an audit entry")
    for command in (audit, promotion):
        command.add_argument("--file", type=Path, default=argparse.SUPPRESS)
    promotion.add_argument("entity_id")
    promotion.add_argument("release_id")
    promotion.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        data = load(args.file)
        if args.command == "promote":
            data = promote(data, args.entity_id, args.release_id, args.reason)
            write_validated(args.file, data)
            print(f"Promoted {args.entity_id} to {args.release_id}; previous releases retained. Review the diff before commit.")
        else:
            count = sum(len(entity["releases"]) for entity in data["entities"])
            print(f"Valid: {len(data['entities'])} entities, {count} releases, {len(data['view']['items'])} root view items; duplicate keys and broken references: 0.")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
