---
type: entity
title: "SKHASH"
tags: ["seismic-processing"]
sources: ["skousmal-2024-skhash.pdf","skhash-manual-v1.1.pdf"]
related: ["skousmal-2024-skhash","skhash-manual-v1.1","phasenet","uncertainty-and-quality-control","version-and-evidence-gaps"]
created: "2026-10-06"
updated: "2026-10-06"
---

# SKHASH

SKHASH is a Python package for computing earthquake focal mechanisms from P-wave first-motion polarities and S/P amplitude ratios. It is largely based on the HASH algorithm (Hardebeck & Shearer 2002, 2003), and keeps HASH's central design: instead of a single best-fit solution, it computes a suite of solutions spanning the expected errors in polarities and takeoff angles, and uses that suite to estimate focal-mechanism uncertainty ([skousmal-2024-skhash](../sources/skousmal-2024-skhash.md), PDF pp. 1–2).

**Input:** earthquake catalog (hypocenters and uncertainties), station table, P first-motion polarities, optional S/P amplitude ratios, layered velocity model(s). **Output:** strike/dip/rake solution suites with per-event best solutions, quality grades A/B/C/D, per-station polarity and amplitude misfit reports, and outputs that help identify metadata problems such as incorrectly reported station polarity reversals ([skousmal-2024-skhash](../sources/skousmal-2024-skhash.md) — see [manual](../sources/skhash-manual-v1.1.md)).

Distinguishing features relative to classic HASH:

- Weighted P polarities are supported, including weights from machine-learning pickers such as PhaseNet+, cross-correlation consensus, and imputation techniques ([skousmal-2024-skhash](../sources/skousmal-2024-skhash.md), PDF p. 3).
- S/P amplitude ratios (traditional, machine-learning, or cross-correlation consensus) can further constrain solutions (PDF pp. 3–4).
- Earthquake 3D locations and velocity models are varied while searching for acceptable solutions, so source–receiver azimuths reflect errors from locations and models in addition to takeoff angles (PDF p. 2).
- Quality grades use the original HASH criteria; the reporting of individual and collective polarity/S-P misfits makes it easier to spot bad metadata and reversed stations (PDF pp. 1, 5).

In this workflow collection, SKHASH is the focal-mechanism stage, consuming PhaseNet+ weighted polarities from the picking stage together with measured S/P ratios. Execution uses the vendored v1.1 source with four documented compatibility patches; see [version-and-evidence-gaps](../queries/version-and-evidence-gaps.md) for the version-matching note.
