---
type: source
title: "PhaseNet: a deep-neural-network-based seismic arrival-time picking method"
tags: ["seismic-processing"]
sources: ["zhu-2019-phasenet.pdf"]
related: ["phasenet","phase-picking","catalog-construction","version-and-evidence-gaps"]
created: "2026-09-14"
updated: "2026-09-14"
authors: ["Weiqiang Zhu","Gregory C. Beroza"]
year: 2019
venue: "Geophysical Journal International 216, 261–273"
url: "https://doi.org/10.1093/gji/ggy423"
source_file: "zhu-2019-phasenet.pdf"
original_filename: "phasenet.pdf"
evidence_status: "local-primary-source"
---

# PhaseNet: a deep-neural-network-based seismic arrival-time picking method

**Citation:** Weiqiang Zhu; Gregory C. Beroza (2019). Geophysical Journal International 216, 261–273. DOI: 10.1093/gji/ggy423.

**Version note:** Journal article; online publication 13 October 2018, issue year 2019.

## Research problem

Accurate P and S arrival picking is a bottleneck in earthquake monitoring. The paper learns waveform features from analyst-labelled records instead of specifying a detection statistic manually.

## Method and data

PhaseNet is a U-Net-derived, one-dimensional convolutional encoder–decoder. Three-component waveforms are mapped to samplewise probabilities for P arrivals, S arrivals, and noise. Arrival times are selected from probability peaks. Training targets represent manual picks with Gaussian distributions of standard deviation 0.1 s; each input component is demeaned and divided by its standard deviation.

The study uses 779,514 Northern California records with both P and S picks: 623,054 training, 77,866 validation, and 78,592 test samples. Training examples are approximately 30 s at 100 Hz, with 3,001 samples per component. These describe the paper's experiment, not a universal preprocessing contract for every later PhaseNet implementation.

## Reported results

Table 1, physical PDF p. 4, reports the following on the paper's test set. True-positive matching uses a 0.1 s residual threshold.

| Metric | PhaseNet P | PhaseNet S | AR picker P | AR picker S |
|---|---:|---:|---:|---:|
| Precision | 0.939 | 0.853 | 0.558 | 0.195 |
| Recall | 0.857 | 0.755 | 0.558 | 0.144 |
| F1 | 0.896 | 0.801 | 0.558 | 0.165 |

The reported residual standard deviations are 51.530 ms for P and 82.858 ms for S, calculated with a separate 0.5 s residual cutoff. These are published results, not measurements reproduced in this workspace.

## Scope and limitations

The main evaluation concerns already detected earthquake records. The discussion explicitly identifies additional non-seismic training signals as necessary for robust continuous detection. Model probabilities are not, by themselves, calibrated arrival-time uncertainties. This paper describes original PhaseNet, not PhaseNet+ or first-motion polarity estimation.

## Relevance to this collection

PhaseNet supplies arrivals to an association algorithm such as [gamma](../entities/gamma.md). It does not replace network association, absolute location, or relative relocation.

## Evidence and reading guide

- [PDF p. 4](../../raw/sources/zhu-2019-phasenet.pdf#page=4) — Dataset, preprocessing, and Table 1.
- [PDF p. 5](../../raw/sources/zhu-2019-phasenet.pdf#page=5) — Training targets and network design.
- [PDF p. 11](../../raw/sources/zhu-2019-phasenet.pdf#page=11) — Continuous-detection caveat and discussion.
- [PDF p. 12](../../raw/sources/zhu-2019-phasenet.pdf#page=12) — Probability peaks, threshold discussion, and conclusions.

- [Original PDF](../../raw/sources/zhu-2019-phasenet.pdf)
- [Complete page-numbered extracted text](../../raw/assets/extracted/zhu-2019-phasenet.md)

## Connected knowledge

[phasenet](../entities/phasenet.md) · [phase-picking](../concepts/phase-picking.md) · [catalog-construction](../synthesis/catalog-construction.md) · [version-and-evidence-gaps](../queries/version-and-evidence-gaps.md)
