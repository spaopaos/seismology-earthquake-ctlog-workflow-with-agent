---
type: concept
title: "Earthquake Phase Association"
tags: ["seismic-processing"]
sources: ["zhu-2022-gamma.pdf","zhou-2022-palm.pdf"]
related: ["gamma","phase-picking","absolute-location"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Earthquake Phase Association

Association determines which station arrivals can be explained by the same earthquake. It must reject or leave unassigned observations that do not support a coherent source hypothesis.

[gamma](../entities/gamma.md) treats event membership probabilistically using arrival-time and optional amplitude residuals. In dense sequences, station-dependent moveout helps distinguish arrivals that are close on a simple time axis. The required predictions depend on geometry, phase type, and a travel-time model.

**Recommended evidence to preserve:** pick-to-event assignments, unassociated picks, station and phase counts, residual distributions, and the model/configuration used. This is a practical synthesis rather than a fixed output format prescribed by the papers.

**Evidence:** [zhu-2022-gamma](../sources/zhu-2022-gamma.md), PDF pp. 1–5; [zhou-2022-palm](../sources/zhou-2022-palm.md), PDF workflow discussion.

Association-stage source estimates should be checked before feeding [absolute-location](absolute-location.md) or interpreting spatial patterns.
