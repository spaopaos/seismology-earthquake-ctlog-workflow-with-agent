# Post-MESS workflow validation — 2026-09-15

Workflow revision: 0.3.0-dev. Original v0.2.0 validation records are retained as historical records.

## Executed checks

The complete current regression suite passed **27 tests** in 15.028 s: 10 knowledge/routing checks, 8 portability checks, and 9 post-MESS tests. It used the existing runtime.local.json mapping; no environment installation or upgrade was performed.

The new tests exercise independent PhaseNet arrival provenance, missing/ambiguous/shared-pick rejection, CC origin correction across a minute boundary, below-threshold reference events on the first side of a CC pair, missing CT, duplicate CC, both-data weighting, stale CC evidence rejection, and the final CLI stage route.

Native tests use the pinned ph2dt and HypoDD binaries. A labeled synthetic homogeneous regional fixture contains five detection events plus one template reference and eight stations. Joint mode retains both CC and CT constraints, recovers centered relative geometry with median error below 20 m for this fixture, and also passes the original CT-only path. This tolerance is a synthetic test assertion, not a field-data accuracy statement.

Three independent native runs publish exactly three detection catalogs with five detection IDs each; reference ID 9 is kept separately. The new output contract passes schema and artifact checks. The publication unit test stubs already-validated upstream contracts; it is not a full raw-waveform-to-catalog end-to-end scientific benchmark.

A schema-reference scope issue exposed by publication testing was fixed in the new schema using explicit document-qualified references; the existing validator environment was retained. The final complete suite passes after that fix.

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
