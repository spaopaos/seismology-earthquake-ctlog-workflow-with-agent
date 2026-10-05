# Focal mechanisms — execution binding

SKHASH v1.1 grid search over first-motion polarity (PhaseNet+ continuous
polarity score, weighted) plus measured S/P amplitude ratios, on the
first-round hypoDD tier catalog. Quality grades A/B/C/D use the original
HASH (Hardebeck & Shearer 2002) criteria and must not be tuned to inflate
grade A; iteration is only allowed through data-quality control.

Region-dependent values are user decisions: the layered P velocity model,
the polarity threshold (0.3 = the HASH impulsive-picks-only equivalent
mapped onto the continuous score), delmax, and the polarity-reversal list.
A station is only accepted as reversed when colocated-pair agreement is
clearly below 50% AND the post-reversal mechanism agreement jumps above
60%; remaining ~50% agreement stations are deep-learning polarity noise,
and flipping them risks overfitting.

The paper is method background; the v1.1 manual is the version-matched
operating reference (the vendored source carries four numpy>=2/pandas3
compatibility patches — see VENDORED_PATCHES.md; do not substitute a
pip-installed SKHASH).

- [Stage policy](../../skills/seismic-focal-mechanism/SKILL.md)
- [Vendored provenance + patches](../../knowledge/repos/SKHASH/VENDORED_PATCHES.md)
- [Inputs builder](../../skills/seismic-focal-mechanism/scripts/1_build_inputs.py)
- [Event waveform library](../../skills/seismic-focal-mechanism/scripts/2_cut_event_waveforms.py)
- [S/P amplitudes](../../skills/seismic-focal-mechanism/scripts/3_measure_sp_amplitudes.py)
- [Reversal QC](../../skills/seismic-focal-mechanism/scripts/4_check_polarity_reversal.py)
- [Runner](../../skills/seismic-focal-mechanism/scripts/5_run_skhash.py)
- [Catalog parser](../../skills/seismic-focal-mechanism/scripts/6_parse_mechanisms.py)
- [Initial settings](../../../configs/pipeline.example.json)

## Wiki reading route

- [SKHASH](../library/wiki/entities/skhash.md)
- [SKHASH paper (Skoumal et al. 2024)](../library/wiki/sources/skousmal-2024-skhash.md)
- [SKHASH v1.1 manual](../library/wiki/sources/skhash-manual-v1.1.md)
- [PhaseNet](../library/wiki/entities/phasenet.md)
- [Uncertainty and quality control](../library/wiki/concepts/uncertainty-and-quality-control.md)

Strong-motion events can lose polarity confidence at near stations
(amplitudes 6–10× grade-A events) and be rejected on takeoff-angle gaps;
that is expected HASH-family behavior, not a defect. Strike/rake statistics
must be circular.
