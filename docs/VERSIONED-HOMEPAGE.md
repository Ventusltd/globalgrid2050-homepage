# Versioned homepage

The homepage display is owned here. The existing globalgrid2050 domain publisher and all app URLs remain in place. Canonical domain/data ownership stays in the federation registry; this configuration is a navigation consumer, not a second database registry.

## Files to edit

`data/homepage.json` contains product identities, release records, an explicit operative release per product, ordered homepage selections and development ticker links. CSS owns the existing retro colours and typography. Data updates must not change those styles.

Grain: one entity per enduring product; one release per entity/release-ID pair. The operative pointer must reference an available release of that product. Releases use permanent IDs; their labels may be human-readable. Existing imported product IDs remain stable. New product variants may have a parent_id; versions belong in releases, not new entities.

## Release sequence

1. Add a release under its existing entity with a new permanent ID, label, URL, source_ref and actual published_at (null if unknown). Start with status candidate. Prefer immutable dated app URLs; do not overwrite a historical build.
2. Verify the app separately. This homepage validator does not certify engineering functionality. Once accepted, change its status to available.
3. Run `python scripts/releases.py validate`.
4. Run `python scripts/releases.py promote kuiper RELEASE_ID --reason "Verified release and accepted for operation"`.
5. Review and commit the configuration diff. The old release stays intact, an audit entry records the pointer change, and the selected operative release appears above all other releases. Merely adding a newer candidate does not promote it.

Rollback uses the same promote command with the earlier release ID. It retains both records and adds another audit entry. A promotion edits the catalogue only: it does not deploy or replace the actual application. If the application has its own current.json, promote and verify that app using its owner workflow first, then update this catalogue.

## Historical links

For operative releases, url opens the app. For older entries, archive_url is used if present, otherwise url. archive_kind manifest is explicitly labelled Release record: it preserves a composition specification, not a promise of an executable old app. Kuiper's current loader lacks a general historical-composition replay feature, so its pinned manifest is retained honestly as a record. The dated one-wafer page is a runnable archive link. GridAtlas retains its existing immutable composition manifest. This avoids repointing old version labels at whatever a mutable current route later serves.

## Development bar

The development list names actual linked work and is independent of the operative release list. It does not imply completion, generate fake events or change product status. The bar has pause, hover/focus pause and a static reduced-motion presentation. Initially it links to the verified Kuiper drawing-engine repository.

## Limits and sources

This is a bounded small-catalogue implementation, not the proposed billion-record API. Search filters catalogue metadata in the browser. There is no live database subscription or fabricated market data. The separate local CuPy probe measured numerical filters and aggregates; it is not silently embedded in this frontend.

Sources: accepted domain navigation at globalgrid2050 commit 7c64560d282f3412a3dfd79939e236a37ee5e8da; kuiper/current.json generation 202609200300; GridAtlas current generation 202609241334 (V9.156); existing timestamped Pipeline News and one-wafer routes; existing V7 sandbox route. Unknown historical publication times are null. Existing data/catalog.json and doctrine documents are retained.

The Pages workflow validates keys/references and publishes only index, two assets, catalogue and .nojekyll, with a 1 MB uncompressed homepage bundle budget. It does not copy apps or raw data. A domain importer must pin the source commit and verify file hashes; source code and configuration have only one editable owner.
