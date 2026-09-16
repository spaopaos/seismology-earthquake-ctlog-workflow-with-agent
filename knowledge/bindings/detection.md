# Detection — execution binding

The PALM paper is method background. Current execution uses the pinned integrated PALM implementation, medium-only templates, one scan/global association and CC>=0.4/0.6/0.8 independent products. These are project choices, not universal thresholds derived from the paper.

## Read in this order

1. The current stage skill and this version binding.
2. Relevant Wiki pages for explanation and context.
3. The pinned source/manual for implementation-specific numbers, fields or units.
4. Current data calculations/trials and actual effective configuration for decisions.

## Current implementation evidence

- [workflow_policy](../../skills/seismic-detection/SKILL.md)
- [pinned_implementation](../../knowledge/repos/PALM/MFT_src/associate_mft.py)
- [actual_scan_workflow](../../skills/seismic-detection/scripts/run_mess.py)
- [actual_threshold_products](../../skills/seismic-detection/scripts/export_cc_catalogs.py)

## Wiki reading route

- [PALM and MESS](../library/wiki/entities/palm-mess.md)
- [An Earthquake Detection and Location Architecture for Continuous Seismograms: Phase Picking, Association, Location, and Matched Filter (PALM)](../library/wiki/sources/zhou-2022-palm.md)
- [Matched-Filter Earthquake Detection](../library/wiki/concepts/matched-filter-detection.md)
- [From Waveforms to an Expanded Earthquake Catalog](../library/wiki/synthesis/catalog-construction.md)
- [Version and Evidence Gaps](../library/wiki/queries/version-and-evidence-gaps.md)

The original Wiki records its eight-source scope. These bindings add execution context; they do not claim independent scientific validation of every Wiki statement.
