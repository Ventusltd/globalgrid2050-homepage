# One catalogue, several views

`data/homepage.json` is the maintained app catalogue. The nests and searchable
table are views of the same records. A ticker is a discovery aid, not the index:
falling out of its activity ranking must never delete a catalogue record.

Each entity has a permanent `id`; releases have a key formed from that entity ID
and their release ID. Keep IDs when changing titles, categories or URLs. Use
`parent_id` for a child tool and `view.items` for top-level nests. An operative
release points to an available app. Retain earlier release records when promoting
a replacement, using `scripts/releases.py promote` with a reason.

`data/presentation.json` selects four curated highlights by entity ID and sets
the table page size. Highlights answer where to begin; the activity ticker
answers what has changed; the catalogue retains the full registered collection.
Changing a highlight does not remove the underlying app. The initial editorial
roles are Explore, Design, Markets and Learn.

Add or recover apps by editing this catalogue, not the JavaScript. Grid engines,
market intelligence, materials and cable engineering have distinct purposes;
their titles and descriptions should say what the tools actually do. In
particular, an AC block diagram is not a single-line diagram or a complete
electrical design. Do not infer approval from the existence of a drawing.

Run `python scripts/releases.py validate` and the tests before publishing.
The static fallback is regenerated from this same catalogue for users without
JavaScript using `python scripts/build_homepage_fallback.py`. Hosted browser
checks must pass before Pages deployment. The main
domain imports a reviewed, hash-pinned owner commit; publishing this owner alone
does not automatically replace the main domain.

## Activity ticker

`config/active-pages.yaml` is JSON-compatible YAML, read with the Python standard
library. Run `python scripts/fetch_active_pages.py` to update the separate
`data/active-pages.json` feed. `--check` validates the saved feed offline.

The fetcher samples public repositories and ranks verified live app pages using
default-branch commits within its configured window. Repository and commit caps
are recorded in the feed. Apps sharing a repository share its activity count;
this is not a measure of product quality or an exhaustive estate audit.
GitHub source pages are excluded from app destinations. Pages hosting on
github.io is allowed. Failures preserve the previous feed. No paused collector
or federation workflow needs to be enabled for this view.

## Growth

This is a small, version-controlled catalogue, not a billion-row database.
As it grows, keep the IDs and relationships while moving delivery to indexed,
paginated search. The browser should request a bounded result page rather than
download the whole estate. Data repositories own their large datasets; this
homepage owns the routes into them.

The current implementation paginates a small downloaded JSON catalogue. It does
not implement a million-record backend. A future service should preserve these
logical keys: app `id`; release `(app_id, release_id)`; category `id`; membership
`(category_id, app_id)`; and append-only promotion records. Title, URL and row
position must never become an app's identity. Category membership can become
many-to-many without cloning an app's ID.

Use indexed search and stable cursor ordering, such as `(sort_key, app_id)`,
with bounded responses. Fetch release history only when requested. A snapshot
or revision token should keep a paginated result consistent while data changes.
Retired records should retain their ID and history. These are migration rules,
not a claim that GitHub Pages provides a database or server-side search.
