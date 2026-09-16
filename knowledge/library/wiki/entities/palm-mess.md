---
type: entity
title: "PALM and MESS"
tags: ["seismic-processing"]
sources: ["zhou-2022-palm.pdf"]
related: ["zhou-2022-palm","matched-filter-detection","hypodd","catalog-construction"]
created: "2026-09-14"
updated: "2026-09-14"
---

# PALM and MESS

PALM combines an initial picking–association–location module (PAL) with a matched-filter expansion module (MESS). MESS stands for Match, Expand, Shift, and Stack.

**Input:** continuous seismic data; MESS additionally requires a template catalog and template waveforms. **Output:** an expanded event catalog, correlated arrival observations, and inputs for subsequent relocation.

Peak expansion accommodates timing differences between templates and candidate events before travel-time shifting and multi-station stacking ([zhou-2022-palm](../sources/zhou-2022-palm.md), PDF pp. 6–7).

The original PAL picker combines STA/LTA and kurtosis. Substituting PhaseNet and GaMMA produces an adapted workflow. Template coverage and location quality remain critical to catalog interpretation.
