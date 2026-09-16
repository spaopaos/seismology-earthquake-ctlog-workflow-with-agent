# Validation scope — release 0.1.0

These checks were actually run using the copied package and relocated existing runtimes. They establish the listed execution and interface behaviors. They do not establish scientific accuracy in an unobserved region.

| Check | Result |
|---|---|
| Three offline environment archives extracted to a new path | PASS; dependency imports and full JSON Schema available |
| Package copied to an unrelated directory, without vendor Git metadata | PASS; source, binary and weight checks use the copied package |
| Portability regression tests | 8 PASS: network/station collisions, long aliases, native southern/western coordinates, interval bounds, normalized identity/polarity/validity flags, source tampering, dateline aperture |
| HYPOINVERSE official testone | PASS; SUM and ARC byte-identical to bundled references |
| Actual PhaseNet+ CPU inference | PASS on small HH/HN inputs and a full-day labeled synthetic archive; zero-pick CSV, QC and contract handled correctly |
| Existing observations, 2026-03-06, starting at standardized picks | GaMMA 85 events from 3640 eligible picks, eps=10.0 s; HYPOINVERSE 85 locations |
| HypoDD tiers | Medium READY: 24 events, DAMP=100.0; loose/strict UNAVAILABLE because current trials did not support a final DAMP |
| MESS independent CC 0.4/0.6/0.8 catalogs | 48 / 22 / 14 events; schemas, artifacts and references checked |

The numeric integration used explicit existing inputs. It did not reprocess a new observed region or repeat observed-data PhaseNet+ inference. Synthetic data only tests interfaces and model execution. Location depth uncertainty remains substantial; native solutions and residuals are not accuracy ground truth.

A second physical machine, a genuinely new observed region, an independent agent and GPU execution are NOT_TESTED. Run destination preflight and a representative regional pilot before a large analysis. Do not describe these local checks as those external validations.

The current initial regional configuration differs from the earlier case's implicit search bounds and now preserves full station/location identity. Catalog counts are records of this run, not a claim of an improved or optimal scientific catalog.

Machine-readable evidence is in validation.json. Private waveforms, source responses and developer-specific case paths are not distributed. The original full logs remain in the packaging workspace.
