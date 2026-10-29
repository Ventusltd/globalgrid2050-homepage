# Changes

## 29 October 2026 - privacy notice

- Add a collapsed "Privacy" notice to the homepage footer, below the disclaimer. It is one plain-English statement covering the homepage, GridAtlas, Pipeline News and the Energy Transition Simulator. It says there are no analytics, no cookies of our own and no accounts; that GitHub Pages logs visitor IP addresses for security; which other services each app contacts and when; what is stored on the device and how to clear it; and what the statement does not cover.
- The text is the same as Ventusltd/gridatlas docs/PRIVACY.md. URLs are shown as text, not links, because the homepage links only to apps.
- It lives in index.html and versioned-homepage.css, so the seven-file bundle and its importer are unchanged. The domain shows it only after the owner accepts this commit and globalgrid2050's catalogue/homepage-owner.json pin moves to it (docs/GRIDATLAS-RELEASE.md step 2).

## 29 October 2026 - GridAtlas v9.172 and one-command GridAtlas releases

- GridAtlas operative release is now V9.172 - 28 October 2026 (generation 202610281340); V9.156 is retained as an archived release with its composition manifest.
- GridAtlas description mentions the optional UK lightning overlay (observed optical flashes, 12-month history) linked to nearest substations.
- Add scripts/release_gridatlas.py and docs/GRIDATLAS-RELEASE.md so the next GridAtlas release is one command plus the domain pin.
- Run the publication checks on pull requests (pr-checks.yml); nothing deploys from it.
- Make the active-pages network-failure test independent of today's date.

## 25 September 2026 - build highlights and connected identities

- Preserve the top search, retro palette, existing nests, explicit versions and archive.
- Add Identity Registry as the fifth nest, linking its tested public demonstration release.
- Show two compact In build cards driven by development configuration; search their descriptions independently of the app nests.
- Expand the full-width ticker to available app links plus current development links, with a 65-second cycle, pause, keyboard access and reduced-motion behaviour.
- Run desktop/mobile browser checks in the existing publication workflow before deployment.
- Inspection connectors remain labelled in development; no live inspection or billion-row service is implied.

## 25 September 2026 - versioned nests

- Restore a working configurable homepage with the existing retro theme and four selected nests; label Kuiper without the Original prefix.
- Add explicit operative pointers, nested release history, candidate separation, promotion audit and rollback.
- Add bounded metadata search and a full-width development ticker with pause and reduced-motion behavior.
- Keep static launch links if JavaScript or configuration loading fails.
- Publish a validated, allowlisted small bundle; preserve existing doctrine and legacy catalogue.
- No domain transfer, bulk data migration or billion-record backend is included.
