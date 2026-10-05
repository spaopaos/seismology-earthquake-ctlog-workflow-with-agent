---
type: source
title: "SKHASH v1.1 Manual: A Python Package for Computing Earthquake Focal Mechanisms"
tags: ["seismic-processing"]
sources: ["skhash-manual-v1.1.pdf"]
related: ["skhash","skousmal-2024-skhash","uncertainty-and-quality-control","version-and-evidence-gaps"]
created: "2026-10-06"
updated: "2026-10-06"
authors: ["Robert J. Skoumal","Jeanne L. Hardebeck","Peter M. Shearer"]
year: 2025
venue: "U.S. Geological Survey software manual, SKHASH v1.1 (last modified 20 May 2025)"
url: "https://code.usgs.gov/esc/skhash/"
source_file: "skhash-manual-v1.1.pdf"
original_filename: "SKHASH_manual.pdf"
evidence_status: "local-primary-source"
---

# SKHASH v1.1 Manual

**Citation:** Robert J. Skoumal, Jeanne L. Hardebeck, Peter M. Shearer. SKHASH v1.1 manual, last modified 20 May 2025. U.S. Geological Survey.

**Version note:** This manual documents SKHASH v1.1 (upstream snapshot 2025-12-17). It is version-matched to the vendored `knowledge/repos/SKHASH` source used by this workflow, except for four documented numpy>=2/pandas3 compatibility patches that do not change documented behavior (see `knowledge/repos/SKHASH/VENDORED_PATCHES.md`).

## Document purpose

Operational reference for running SKHASH: control-file syntax, every input file format (polarity files, S/P amplitude files, station file, polarity-reversal file, catalog, velocity models), program controls, output files, and the weight/quality code conventions. It is the authority for implementation-specific numbers, fields and units, unlike the paper, which is method background.

## Core operating model

`SKHASH path_to/control_file.txt [--num_cpus=N]`. A single control file declares input paths (catalog, station file, polarity file(s), amplitude file(s), optional polarity-reversal and station-correction files, one or more velocity models), output paths, and search controls (minimum polarity count, number of trials, damping of the velocity/depth perturbations, grid spacing, quality criteria).

## What to extract when implementing

1. Polarity inputs come in several formats (`$fpfile` traditional, `$impfile` imputed, `$conpfile` cross-correlation consensus, `$dlpfile` deep-learning weighted); the deep-learning file carries continuous polarity scores whose magnitude is the weight (PDF pp. 3, 15).
2. S/P amplitude files (`$ampfile`, `$relampfile`) carry raw amplitudes or ratios; SNR gating (`$ratmin`) and ratio computation are applied by the program (PDF p. 4).
3. The polarity-reversal file (`$plfile`) flips listed station channels between start/end times — the documented mechanism for correcting hardware-reversed instruments (PDF p. 5).
4. The catalog file carries per-event location uncertainties that drive the location perturbation trials; velocity model files are depth–Vp pairs and must be strictly increasing in Vp (PDF pp. 6–7).
5. Quality grades A/B/C/D and their criteria are configurable program controls; the defaults are the HASH originals and should not be relaxed to inflate grade counts (PDF p. 12).

## Scope and limitations

The manual documents upstream v1.1 behavior only. The four compatibility patches in the vendored copy are recorded separately; a pip-installed SKHASH is not the tested implementation of this workflow. Parameter defaults in the manual are starting points, not region-fitted optima; polarity thresholds, reversal lists and velocity models remain user decisions recorded in the run configuration.

## Relevance to this collection

This is the version-matched operating reference for the focal-mechanism stage in [catalog-construction](../synthesis/catalog-construction.md); method background is in the [paper](skousmal-2024-skhash.md).

## Evidence and reading guide

- [PDF p. 1](../../raw/sources/skhash-manual-v1.1.pdf#page=1) — Overview, invocation, control-file concept, file-format index.
- [PDF p. 2](../../raw/sources/skhash-manual-v1.1.pdf#page=2) — Bundled examples.
- [PDF p. 3](../../raw/sources/skhash-manual-v1.1.pdf#page=3) — Polarity file formats (`$fpfile`, `$impfile`, `$conpfile`, `$dlpfile`).
- [PDF p. 4](../../raw/sources/skhash-manual-v1.1.pdf#page=4) — S/P amplitude file formats (`$ampfile`, `$relampfile`).
- [PDF p. 5](../../raw/sources/skhash-manual-v1.1.pdf#page=5) — Station corrections, station file, polarity-reversal file (`$plfile`).
- [PDF p. 6](../../raw/sources/skhash-manual-v1.1.pdf#page=6) — Catalog file; velocity-model file format (strictly increasing Vp).
- [PDF p. 8](../../raw/sources/skhash-manual-v1.1.pdf#page=8) — Output file paths; direct program controls (minimum polarities, trials).
- [PDF p. 12](../../raw/sources/skhash-manual-v1.1.pdf#page=12) — Quality criteria A–D; grid spacing and lookup-table bins.
- [PDF p. 15](../../raw/sources/skhash-manual-v1.1.pdf#page=15) — Weight code conventions (`abs(weight)` semantics).

- [Original PDF](../../raw/sources/skhash-manual-v1.1.pdf)
- [Complete page-numbered extracted text](../../raw/assets/extracted/skhash-manual-v1.1.md)

## Connected knowledge

[skhash](../entities/skhash.md) · [skousmal-2024-skhash](skousmal-2024-skhash.md) · [uncertainty-and-quality-control](../concepts/uncertainty-and-quality-control.md) · [version-and-evidence-gaps](../queries/version-and-evidence-gaps.md)
