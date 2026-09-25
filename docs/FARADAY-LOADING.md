# Faraday pulse: loading lessons

Source review, 25 September 2026. This is a transfer of design patterns, not a
claim that a circuit simulator supplies a database or that GPU throughput
measures web-search latency. No upstream code was copied into this change.

## Provenance

- [Faraday](https://github.com/Ventusltd/faraday), commit `e439b450`,
  `apparatus/cells.mjs`: `compile`, `state`, `read` and `settles` model timed NAND
  dependencies. Reads request particular outputs; a per-read Map memoizes
  intermediate key/tick results. The transferable idea is demand-driven work
  with an explicit state/version. It is not a network search implementation.
- [GridAtlas](https://github.com/Ventusltd/gridatlas), commit `173b329`:
  `executeSearch` uses an active query serial, two-character threshold and
  180 ms debounce; global search is explicit. Its on-demand bridge deduplicates
  requests, evicts failures and closes database connections.
- [Pipeline News](https://github.com/Ventusltd/pipelinenews), commit `498009`:
  compact search text, detail partitions, four concurrent detail loads and
  `hydrateDetail` retain the canonical row if enrichment fails. Search windows
  are bounded; optional news/charts wait until after initial work. Some core
  enrichment still blocks boot, so it is not a universally lazy implementation.
- The older [published Pipeline workspace](https://globalgrid2050.com/uk_renewables_pipeline/202609082224/)
  boots `scripts/app-v9-8.js`; `plugins/projects-v9-8.js` renders 20-row pages
  after downloading the model. Its news replica selection waits for both
  responses without a timeout. Do not confuse DOM pagination with network
  pagination or attribute newer repository behavior to this older release.
- [Electricity V6](https://globalgrid2050.com/uk_energy_tracking_v6/), source
  path `uk_energy_tracking_v6/` in globalgrid2050 at `1f8ecfe9`: price loaders
  choose annual partitions or daily aggregates and share in-flight promises.
  Generation selects a resolution tier. Failures cached as empty arrays and
  unconditional cache-busting are patterns to improve, not reproduce.
- [Federated electricity UI](https://github.com/Ventusltd/gb-electricity-ui)
  at `5b4533914bb2bcad7f5ea697af00faf67cf626cc` is explicitly a data-disabled
  shell. Its illustrative curves are not evidence of a working data loader.

## Applied to this homepage

The static shell and curated links survive failed data requests. Core JSON
requests have an eight-second abort deadline. An optional ticker cannot prevent
catalogue use. A failed configuration leaves the static fallback in place.

Search text is computed once per entity and reused. Parent/child relationships
are indexed once rather than rescanning the catalogue for every nest. Search
still covers every registered entity and release, not only the visible page.
At most the configured page size is rendered into the table. Version details
are constructed on demand and reused while their row remains mounted.

These are bounded improvements to a small, fully downloaded catalogue. They
do not provide server-side pagination or remotely loaded release histories.
The hosted browser suite covers off-page search, pagination, failed data,
invalid page sizes, optional-feed isolation and on-demand detail rendering.

## Contract for the large-catalogue implementation

1. Read a small manifest carrying a dataset revision. Search an index with a
   query, filters, stable sort and a maximum of 25 results per cursor page.
2. Debounce input; abort superseded requests and reject responses whose query
   serial or revision no longer matches. Cancellation alone is insufficient.
3. Fetch detail partitions only for selected entries. Bound concurrency, share
   in-flight requests, evict rejected promises and permit retry.
4. Cache immutable partitions by revision/hash. Revalidate mutable manifests;
   never serve another revision's detail under the current release identity.
5. Preserve the last valid result during a transient refresh failure and label
   its source date. Keep source time separate from fetch time and show empty,
   loading, stale and failed states separately. Missing values are not zeros.
6. Measure transferred bytes, requests, first useful render, query latency and
   memory on a stated corpus/device. Count catalogue records separately from
   GPU operations. Validate late-response rejection and retry behavior before
   claiming million-row readiness.

Permanent entity IDs, releases, source/licence and scoped review records remain
separate from presentation and activity ranking. Attribution identifies origin;
review identifies what was checked. Neither implies universal engineering
approval or permission to redistribute confidential material.
