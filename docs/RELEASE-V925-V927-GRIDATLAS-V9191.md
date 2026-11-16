# Pipeline V9.25–V9.27 and GridAtlas V9.191 owner promotion

This owner-only change appends three dated Pipeline editions and one GridAtlas
generation. It preserves every previous release and audit entry. COMMAND is the
sole merger; the separate domain restore-point, owner pin and public-root
readback are outside this PR. No human acceptance is inferred.

| Edition | Immutable source commit | Public index SHA256 |
| --- | --- | --- |
| V9.25 / 202611161630 | `60c778d9789b88ce6a803ac84bff9099e423eec2` | `d762ab6f7d5cff70f0b7427b1d524e3fefb5e0ba95e5f08bd95377d46b443a1a` |
| V9.26 / 202611161734 | `53c437fa23debe16036b87ba3d59cfaca3900105` | `4b275043bea6bf30e5573ddb2db5a70f84fd434b20f7806049dac7028d300564` |
| V9.27 / 202611161747 | `fb4bd1baaa50c5102a791cf88b9ef23f3fc89a67` | `ef77a1017c4bd54657f5b2061367aaba3d85170996d642916a49418ac888b419` |

The hashes above identify the merged source files; public readback results are
recorded separately in the PR. A pending edition remains a candidate until its
public bytes match. V9.25 was observed HTTP 200 at 18:08:59 UTC, matching its
17,225-byte source index. Its deploy job completed at 18:08:41 UTC in
[run 43924628537](https://github.com/Ventusltd/globalgrid2050/actions/runs/43924628537).

GridAtlas main `1de35f9eca360a5d80d81542230fef546917f5c5` serves generation
`202611161720`, composition `v9.191`. Its public pointer was read at 18:05:18 UTC:
69,086 bytes, SHA256
`5f7c3fafc789f2b779a9bc7352d8619e7cb9f9ca06724287614dfc73113b27e8`.
The immutable archive index returned HTTP 200, 6,469 bytes, SHA256
`d162f66ae44da79afe92edffdc9f31ea15a85ecf1f7632ce4cb7d1c6ca207b50`.
The deployment completed at 17:50:55 UTC in
[run 43922521166](https://github.com/Ventusltd/gridatlas/actions/runs/43922521166);
[live-byte verification 43922522238](https://github.com/Ventusltd/gridatlas/actions/runs/43922522238)
passed. Distance and nearby-substation screening do not establish grid capacity
or a connection offer.

`scripts/release_gridatlas.py release` and `scripts/releases.py promote` create
the audit entries; `scripts/build_homepage_fallback.py` regenerates the static
links. The catalogue-validation workflow retains all historical assertions and
adds exact new source references and the intended V9.27 operative target.

The preparation passed 20 unit tests, JavaScript syntax, offline ticker checks
and an exact comparison retaining all historical catalogue fields. Hosted
[owner checks 43925701614](https://github.com/Ventusltd/globalgrid2050-homepage/actions/runs/43925701614)
passed the full desktop/mobile browser suite on preparation commit `130752d`.
Local Windows runs encountered `ERR_ADDRESS_IN_USE` while creating a new
browser context; the isolated pagination fixture passed. Final-head PR CI is
required separately. No native Android test is claimed.

V9.25–V9.27 remain software increments: solar source collection is disabled,
independently verified project findings remain zero, global data-centre coverage
is a partial sourced sample, and V9.27 research priority is separate from the
unchanged official register and Solar-1000 selection. No live trend or investment
probability is inferred.
