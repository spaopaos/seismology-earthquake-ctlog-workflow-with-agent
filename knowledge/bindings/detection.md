# Detection — execution binding

The PALM paper is method background. Current execution follows the Eryuan MESS rules through the skill launchers: the full medium-tier hypoDD catalog as the unique template library, one scan/global association, depth offset 0, and CC>=0.4/0.6/0.8 independent products. These are project choices, not universal thresholds derived from the paper.

## Read in this order

1. The current stage skill and this version binding.
2. Relevant Wiki pages for explanation and context.
3. The pinned source/manual for implementation-specific numbers, fields or units.
4. Current data calculations/trials and actual effective configuration for decisions.

## Current implementation evidence

- [workflow_policy](../../skills/seismic-detection/SKILL.md)
- [pinned_implementation](../../knowledge/repos/PALM/MFT_src/associate_mft.py)
- [region_dependent_config_template](../../skills/seismic-detection/scripts/config_mess.py)
- [template_and_station_inputs](../../skills/seismic-detection/scripts/1_prepare_inputs.py)
- [scan_workflow](../../skills/seismic-detection/scripts/2_run_mess_scan.py)
- [threshold_products](../../skills/seismic-detection/scripts/3_export_tiers.py)

## Wiki reading route

- [PALM and MESS](../library/wiki/entities/palm-mess.md)
- [An Earthquake Detection and Location Architecture for Continuous Seismograms: Phase Picking, Association, Location, and Matched Filter (PALM)](../library/wiki/sources/zhou-2022-palm.md)
- [Matched-Filter Earthquake Detection](../library/wiki/concepts/matched-filter-detection.md)
- [From Waveforms to an Expanded Earthquake Catalog](../library/wiki/synthesis/catalog-construction.md)
- [Version and Evidence Gaps](../library/wiki/queries/version-and-evidence-gaps.md)

Region-dependent values (freq band, max stations, trigger threshold, the
magnitude formula for new events) are confirmed with the user per region;
the seven documented pitfalls in the skill are operational constraints, not
suggestions.
