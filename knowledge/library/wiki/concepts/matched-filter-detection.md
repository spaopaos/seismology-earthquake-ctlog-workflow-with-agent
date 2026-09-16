---
type: concept
title: "Matched-Filter Earthquake Detection"
tags: ["seismic-processing"]
sources: ["zhou-2022-palm.pdf"]
related: ["palm-mess","phase-picking","double-difference-relocation"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Matched-Filter Earthquake Detection

Matched filtering searches continuous data for waveforms similar to known templates. Multi-station coherence helps distinguish event-like signals from isolated correlation peaks.

In MESS, the sequence is correlation, peak expansion, travel-time shifting, and stacking. Expansion tolerates deviations from the template's exact moveout. Correlated phase measurements can then support relative relocation.

The template catalog controls which event families and source regions are well represented. Threshold choices also affect candidate counts and false detections. Template self-detections and duplicates from several templates require explicit handling.

A detector's correlation score is not automatically a calibrated probability. More detections do not alone establish improved catalog reliability.

**Evidence:** [zhou-2022-palm](../sources/zhou-2022-palm.md), PDF pp. 6–8 and 10. The parameter values there apply to the Ridgecrest experiment.
