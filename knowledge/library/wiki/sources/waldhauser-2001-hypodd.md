---
type: source
title: "hypoDD — A Program to Compute Double-Difference Hypocenter Locations"
tags: ["seismic-processing"]
sources: ["waldhauser-2001-hypodd.pdf"]
related: ["hypodd","double-difference-relocation","uncertainty-and-quality-control","version-and-evidence-gaps"]
created: "2026-09-14"
updated: "2026-09-14"
authors: ["Felix Waldhauser"]
year: 2001
venue: "USGS Open-File Report 01-113"
url: ""
source_file: "waldhauser-2001-hypodd.pdf"
original_filename: "HYPOdd.pdf"
evidence_status: "local-primary-source"
---

# hypoDD — A Program to Compute Double-Difference Hypocenter Locations

**Citation:** Felix Waldhauser (2001). USGS Open-File Report 01-113. 

**Version note:** hypoDD version 1.0, March 2001; software manual, not the 2000 method paper.

## Document purpose

The manual introduces hypoDD version 1.0 and its companion program ph2dt. It explains data preparation, event linkage, clustering, iterative relocation, weighting, output diagnosis, and error assessment.

## Physical idea and computation

For nearby earthquakes recorded at a common station, much of the travel path is shared. Differencing the observed arrival times suppresses common propagation errors and makes the relative source separation easier to constrain. The algorithm minimizes observed-minus-predicted differential-time residuals while updating event positions and origin times.

Catalog arrival differences and waveform cross-correlation measurements can be used separately or together. ph2dt constructs suitable event pairs from catalog phase data; hypoDD performs weighted iterative inversion with SVD or damped LSQR. Event linkage and station geometry remain essential even with precise differential times.

## Parameter and diagnostic guidance

The manual describes DAMP values of roughly 1–100 and condition numbers around 40–80 as empirical guidance. It also gives examples in which larger condition numbers still accompany similar internal structures. These are not universal acceptance thresholds.

Assess residual reduction together with hypocenter adjustments, cluster-centroid motion, event retention, and discarded above-ground solutions. The manual recommends that absolute centroid shifts remain small relative to initial-location uncertainty. It explicitly calls for robustness checks and, for LSQR solutions, SVD checks on manageable subsets.

## Scope and limitations

Relative precision does not fix the absolute cluster position. Sparse station coverage, weak event links, unsuitable velocity models, and unstable weighting can compromise depth and relocation. Residual minimization alone is insufficient evidence of a trustworthy catalog.

The source is the 2001 software manual. It is not the full Waldhauser and Ellsworth (2000) method paper, and it does not document every later distribution of HypoDD.

## Relevance to this collection

This is the reference for the relocation stage after [hypoinverse](../entities/hypoinverse.md), and for evaluating the correlation-based relocation used by [palm-mess](../entities/palm-mess.md).

## Evidence and reading guide

- [PDF p. 3](../../raw/sources/waldhauser-2001-hypodd.pdf#page=3) — Physical principle and inversion overview.
- [PDF p. 4](../../raw/sources/waldhauser-2001-hypodd.pdf#page=4) — Catalog and cross-correlation observations.
- [PDF p. 8](../../raw/sources/waldhauser-2001-hypodd.pdf#page=8) — Initial conditions and solution controls.
- [PDF p. 9](../../raw/sources/waldhauser-2001-hypodd.pdf#page=9) — Damping, conditioning, centroid stability, and airquakes.
- [PDF p. 13](../../raw/sources/waldhauser-2001-hypodd.pdf#page=13) — Output interpretation and error assessment.
- [PDF p. 15](../../raw/sources/waldhauser-2001-hypodd.pdf#page=15) — ph2dt reference section.

- [Original PDF](../../raw/sources/waldhauser-2001-hypodd.pdf)
- [Complete page-numbered extracted text](../../raw/assets/extracted/waldhauser-2001-hypodd.md)

## Connected knowledge

[hypodd](../entities/hypodd.md) · [double-difference-relocation](../concepts/double-difference-relocation.md) · [uncertainty-and-quality-control](../concepts/uncertainty-and-quality-control.md) · [version-and-evidence-gaps](../queries/version-and-evidence-gaps.md)
