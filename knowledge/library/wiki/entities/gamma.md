---
type: entity
title: "GaMMA"
tags: ["seismic-processing"]
sources: ["zhu-2022-gamma.pdf"]
related: ["zhu-2022-gamma","phase-association","phasenet","hypoinverse"]
created: "2026-09-14"
updated: "2026-09-14"
---

# GaMMA

GaMMA (Gaussian Mixture Model Association) groups phase observations into earthquake hypotheses under a probabilistic model constrained by expected arrival times and, optionally, amplitudes.

**Input:** picks, station metadata, phase labels, and a travel-time model; compatible amplitude measurements if enabled. **Output:** event hypotheses and pick assignments, with initial source-parameter estimates. **Pipeline role:** network association.

The method uses Bayesian mixture modeling to handle uncertain cluster membership and event counts ([zhu-2022-gamma](../sources/zhu-2022-gamma.md), PDF pp. 3–5). The synthetic and Ridgecrest tests support association capability under the tested conditions.

Treat association estimates as inputs to further quality assessment and location, rather than assuming that they already provide a precise relocated catalog.
