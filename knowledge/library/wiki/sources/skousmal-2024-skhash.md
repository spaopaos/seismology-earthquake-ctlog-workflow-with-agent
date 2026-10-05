---
type: source
title: "SKHASH: A Python Package for Computing Earthquake Focal Mechanisms"
tags: ["seismic-processing"]
sources: ["skousmal-2024-skhash.pdf"]
related: ["skhash","skhash-manual-v1.1","phasenet","uncertainty-and-quality-control"]
created: "2026-10-06"
updated: "2026-10-06"
authors: ["Robert J. Skoumal","Jeanne L. Hardebeck","Peter M. Shearer"]
year: 2024
venue: "Seismological Research Letters 95(4), 2519–2526"
url: "https://doi.org/10.1785/0220230329"
source_file: "skousmal-2024-skhash.pdf"
original_filename: "skhash.pdf"
evidence_status: "local-primary-source"
---

# SKHASH: A Python Package for Computing Earthquake Focal Mechanisms

**Citation:** Robert J. Skoumal; Jeanne L. Hardebeck; Peter M. Shearer (2024). Seismological Research Letters 95(4), 2519–2526. DOI: 10.1785/0220230329.

**Version note:** Published July/August 2024 issue; received 2 October 2023, published online 10 April 2024.

## Research problem

First-motion focal mechanisms of small earthquakes are limited by sparse, noisy polarity observations and uncertain takeoff angles. HASH addressed this with suites of solutions spanning data and angle errors; it was written in Fortran over 20 years ago. SKHASH reimplements and extends this approach in Python with vectorized operations and an efficient C backend.

## Method highlights

- HASH varies hypocentral depths when searching for acceptable solutions; SKHASH additionally varies the 3D earthquake locations and the velocity models, so source–receiver azimuths reflect errors from locations and models in addition to takeoff angles (PDF pp. 2, 4).
- Weighted P-wave first-motion polarities are accepted from traditional or machine-learning picks, cross-correlation consensus, and/or imputation techniques; any combination can be used (PDF pp. 3–4).
- Solutions can be further constrained using traditional, machine-learning, or cross-correlation consensus S/P amplitude ratios (PDF pp. 3–4).
- Improved reporting of individual and collective P polarity and S/P amplitude misfits helps evaluate solution success and identify potential metadata issues, including incorrectly reported station polarity reversals (PDF p. 1).

## Case-study evidence

The paper demonstrates applications to Californian seismicity data (Northern California Earthquake Data Center), shows backward compatibility of HASH inputs, and demonstrates composite focal mechanism solutions; runtimes and efficiency comparisons favor SKHASH over HASH (PDF pp. 5–6). These demonstrations document the software; they are not a benchmark for a new network's parameter choices.

## Scope and limitations

The paper describes the algorithm and software, not a universal parameter policy for a given region. Polarity weighting from machine-learning pickers is an input capability, not a claim that any particular picker's scores are calibrated for a new dataset; threshold mapping (for example, keeping only high-confidence polarities) remains a user decision. The paper's quality grades are HASH's original criteria.

## Relevance to this collection

SKHASH supplies the focal-mechanism stage of [catalog-construction](../synthesis/catalog-construction.md), consuming weighted polarities that [phasenet](../entities/phasenet.md) produces in this workflow. Version-matched operating details live in the [v1.1 manual](skhash-manual-v1.1.md).

## Evidence and reading guide

- [PDF p. 1](../../raw/sources/skousmal-2024-skhash.pdf#page=1) — Abstract; misfit reporting and polarity-reversal detection motivation.
- [PDF p. 2](../../raw/sources/skousmal-2024-skhash.pdf#page=2) — Introduction; FPFIT/HASH heritage; method overview (location/model variation, azimuth computation).
- [PDF p. 3](../../raw/sources/skousmal-2024-skhash.pdf#page=3) — Weighted polarities: machine-learning picks, cross-correlation consensus, imputation.
- [PDF p. 4](../../raw/sources/skousmal-2024-skhash.pdf#page=4) — Inputs (P polarities, S/P ratios); source–receiver azimuth calculation figure.
- [PDF p. 5](../../raw/sources/skousmal-2024-skhash.pdf#page=5) — Optional features; efficiency/runtimes; composite solutions figure.
- [PDF p. 6](../../raw/sources/skousmal-2024-skhash.pdf#page=6) — Application and HASH backward compatibility.
- [PDF p. 7](../../raw/sources/skousmal-2024-skhash.pdf#page=7) — Conclusions; data and resources (code repository, DOI).

- [Original PDF](../../raw/sources/skousmal-2024-skhash.pdf)
- [Complete page-numbered extracted text](../../raw/assets/extracted/skousmal-2024-skhash.md)

## Connected knowledge

[skhash](../entities/skhash.md) · [skhash-manual-v1.1](skhash-manual-v1.1.md) · [phasenet](../entities/phasenet.md) · [uncertainty-and-quality-control](../concepts/uncertainty-and-quality-control.md)
