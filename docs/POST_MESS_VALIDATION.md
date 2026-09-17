# Post-MESS workflow validation — 2026-09-17 (joint lite revision)

Workflow revision: 0.3.0-dev, joint lite redesign. The 2026-09-15 record below is retained as a historical record of the superseded independent-picking design.

## Executed checks — joint lite

The complete regression suite passed **28 checks**: 9 joint-lite post-MESS tests, 10 knowledge/routing checks, 8 portability checks, plus the HYPOINVERSE native smoke. Tests ran with an explicit science-python runtime mapping and the pinned HypoDD binary; no environment installation or upgrade was performed.

The joint-lite tests exercise verbatim first-round dt.ct reuse with its solver-evidence hash tie, tamper rejection on both the reused CT and the adapted CC, empty-CT fail-closed behavior (no silent single-datatype fallback), CC origin correction across a minute boundary, below-threshold reference events on the first side of a CC pair, duplicate CC rejection, both-data weighting under IDAT=3, stale CC evidence rejection, and the final CLI stage route.

Native tests use the pinned HypoDD binary. A labeled synthetic homogeneous regional fixture contains five detection events plus one template reference, eight stations, and a first-round medium-tier ph2dt-style dt.ct. Joint lite retains both CC and CT constraints, recovers centered relative geometry with median error below 20 m for this fixture, and the copied PALM single-block CC-only schedule remains available behind the runner's --cc-only mode. This tolerance is a synthetic test assertion, not a field-data accuracy statement.

Three independent native runs publish exactly three detection catalogs with five detection IDs each; reference ID 9 is kept separately. The output contract (ct_source=first_round_reuse, IDAT=3) passes schema and artifact checks. The publication unit test stubs already-validated upstream contracts; it is not a full raw-waveform-to-catalog end-to-end scientific benchmark.

## Historical record — 2026-09-15 (superseded independent-picking design)

The superseded design matched first-pass independent PhaseNet+ arrivals to MESS windows and regenerated CT through pinned ph2dt. Its complete regression suite passed 27 tests in 15.028 s: 10 knowledge/routing checks, 8 portability checks, and 9 post-MESS tests. The tests exercised independent-arrival provenance, missing/ambiguous/shared-pick rejection and the original joint weighting gates. A schema-reference scope issue exposed then was fixed using explicit document-qualified references; that fix is retained.

## Existing-file input audit

The current local MESS files were separately adapted using the final maintained converter. Original independent PhaseNet arrivals were checked, pinned ph2dt generated CT, and the CC/CT bundle verifier checked origin times, weights, depth offsets and event/station references.

| CC threshold | Independent arrival rows | CC observations | CC pairs | CT observations | CT pairs |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.4 | 2658 | 5121 | 761 | 12066 | 2050 |
| 0.6 | 1663 | 2695 | 370 | 8091 | 1070 |
| 0.8 | 1388 | 1628 | 221 | 7125 | 841 |

These are input counts, not counts of newly relocated earthquakes. The native input unions contain 365/173/130 events including 2/2/1 reference events. The audit does not rerun the full upstream waveform hash graph or the actual region's second-round HypoDD; the latter remains a separate new scientific run.

## Identity and limitations

The updated knowledge snapshot passes identity/link checks with 32 unchanged Wiki pages and eight unchanged source PDFs. Seven stages now have execution routes. Current identity: `seismology-wiki-341dfdceb1c8023a`. New analyses must use a new run directory and keep original upstream lineage; old locks and completed products are not rewritten.

The scientific environments, model weights and native binary identities remain unchanged. Matching native source/build provenance for HypoDD remains unresolved as documented in DEPLOYMENT.md. This update validates input handling, execution and publication, not absolute event identity, field-location accuracy or calibrated magnitude. New independent-arrival values can still have selection dependence because template-derived hints guide matching.

The old maintained-source backup, failed/intermediate test logs, accepted regression log and accepted existing-file input audit are retained in the user's separate workflow-update output directory. No private waveforms or installed environments are included in the workflow source revision.
