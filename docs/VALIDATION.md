# v0.2.0 Wiki integration validation

The knowledge layer and its driver integration were tested. The desktop application and its model-provider API were not used.

| Check | Result |
|---|---|
| Exported corpus | 32 Wiki pages, 8 PDFs, 239 physical pages; original PDFs/text hashes preserved |
| Stage bindings | Six routes, explicit historical/current-version distinctions, current HYPOINVERSE1.40 manual available |
| Knowledge tests | 9 PASS: copied snapshot, links, stage-filtered Chinese queries, source pages/bounds, old-manual scope, tamper rejection, honest available-context status, run-lock/legacy-run refusal, explicit configuration citation, and driver checkpoint coverage across the nine test methods |
| Existing interface tests | 8 PASS |
| Native golden test | HYPOINVERSE testone SUM and ARC remain byte-identical |
| Actual driver invocation | Existing synthetic archive revalidated with new knowledge.lock, context and run-state records |
| Plain Python on a copied package | Stage-aware query works from an unrelated directory, without the desktop app or scientific environment imports |
| Original inputs retained | Live Wiki and v0.1.0 release file hashes unchanged |
| Scientific execution components | 37 stage Python scripts, binaries, weights and runtime manifests unchanged |
| Dependency/knowledge preflight | PASS using the explicitly reused existing runtime mapping |

The numerical case validation belongs to v0.1.0 and is retained as [baseline evidence](BASELINE_VALIDATION_0.1.0.md), with its [original scope and metrics](baseline_validation_0.1.0.json). That case was not rerun for this documentation/access-layer integration. Its scientific accuracy limitations remain.

No independent agent/new-region benchmark, second physical-machine test or complete scientific fact review of all Wiki pages is claimed. Identity/link checks establish retrievability and traceability, not that every cited scientific statement is correct. Automatically provided stage context is not a claim that an agent read the pages.

See validation.json for the measured checks. Source PDFs remain primary evidence; inspect their figures, tables and equations when extraction is insufficient.
