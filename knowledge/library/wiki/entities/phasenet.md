---
type: entity
title: "PhaseNet"
tags: ["seismic-processing"]
sources: ["zhu-2019-phasenet.pdf"]
related: ["zhu-2019-phasenet","phase-picking","gamma"]
created: "2026-09-14"
updated: "2026-09-14"
---

# PhaseNet

PhaseNet is the neural phase picker documented in [zhu-2019-phasenet](../sources/zhu-2019-phasenet.md). It maps three-component waveforms to P, S, and noise probabilities and takes arrival times from probability peaks.

**Input:** three-component waveform windows, with normalization consistent with the model. **Output:** P/S arrival estimates and model scores. **Pipeline role:** single-station phase picking before network association.

The 2019 paper reports F1 values of 0.896 (P) and 0.801 (S) on its particular test set (PDF p. 4). Its discussion separates accurate picking on known events from robust detection in continuous noise (PDF pp. 11–12).

The local source does not document PhaseNet+, first-motion polarity heads, or a validated modern preprocessing recipe. See [version-and-evidence-gaps](../queries/version-and-evidence-gaps.md).
