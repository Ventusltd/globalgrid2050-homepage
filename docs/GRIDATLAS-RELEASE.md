# Releasing a new GridAtlas build on www.globalgrid2050.com

GridAtlas itself is released in `Ventusltd/gridatlas` (its `atlas/current.json`
pointer). Its homepage launch link already opens the canonical live route, so
a GridAtlas release is visible immediately; this procedure only updates the
homepage's version label, description and release history. It does not
promote or test the app. Do it only after the owner has accepted the build.

## 1. This repository (globalgrid2050-homepage)

```sh
git switch -c gridatlas-vX.Y
python scripts/release_gridatlas.py release GENERATION vX.Y --published-at YYYY-MM-DDThh:mm:00Z \
    [--description "One honest sentence about what is new."]
```

The command refuses unless gridatlas `main` serves that generation and
composition version. It appends an `available` release labelled
`VX.Y - D Month YYYY`, links its archive to the immutable
`atlas/v/GENERATION/` route (or the composition manifest if that route does
not exist), promotes it with `scripts/releases.py` (every earlier release and
an audit entry are kept), and rebuilds the no-JavaScript fallback in
`index.html`. Omit `--description` to keep the current text.

Then run the same checks CI runs, commit, open a PR and merge once
`Homepage PR checks` passes:

```sh
python scripts/releases.py validate && python scripts/build_homepage_fallback.py && git diff --exit-code -- index.html
python -m unittest discover -s tests && node --check assets/versioned-homepage.js && python scripts/fetch_active_pages.py --check
```

The merge deploys this repository's own Pages; the domain does not use it.

## 2. Ventusltd/globalgrid2050 (the domain publisher)

```sh
python scripts/release_gridatlas.py pin origin/main   # in this repo, after fetching the merge
```

prints the new `catalogue/homepage-owner.json` (commit plus seven SHA-256s).
In globalgrid2050, follow `homepage_versions/README.md`: dispatch the
`homepage-restore-point-check.yml` workflow, save the next numbered
`homepage_vNNN.html` snapshot of the currently served homepage with its
`-metrics.json` and README entry, replace the pin, run
`python scripts/import_homepage_owner.py` locally (then discard the generated
`homepage-shell/` and `index.html` changes), and open a PR.

Merging it pushes `catalogue/**` to `main`, which triggers
`deploy-pages.yml` (it imports the pinned bundle during the build). If it did
not start, dispatch it:
`gh api -X POST repos/Ventusltd/globalgrid2050/actions/workflows/deploy-pages.yml/dispatches -f ref=main`.

## 3. Verify served bytes

Fetch `https://www.globalgrid2050.com/homepage-shell/data/homepage.json` and
compare its SHA-256 with the pinned `data/homepage.json` hash, and check the
homepage shows the new label and description.
