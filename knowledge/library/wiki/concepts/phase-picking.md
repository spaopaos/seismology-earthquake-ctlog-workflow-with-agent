---
type: concept
title: "Seismic Phase Picking"
tags: ["seismic-processing"]
sources: ["zhu-2019-phasenet.pdf","zhou-2022-palm.pdf"]
related: ["phasenet","palm-mess","phase-association"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Seismic Phase Picking

Phase picking estimates when a seismic phase arrives at a station and labels it, commonly as P or S. Picking quality involves both identifying the correct phase and measuring its onset accurately.

[phasenet](../entities/phasenet.md) learns samplewise class probabilities from labelled waveforms. PAL's original picker combines amplitude-change and kurtosis information. Their published evaluations use different datasets and matching definitions, so reported scores should not be treated as a common benchmark.

For a reusable pick record, preserve station identity, channel/component convention, timestamp, phase label, confidence definition, and relevant waveform provenance. This data-contract recommendation is a synthesis from the papers' input requirements.

**Evidence:** [zhu-2019-phasenet](../sources/zhu-2019-phasenet.md), PDF pp. 4–5 and 11–12; [zhou-2022-palm](../sources/zhou-2022-palm.md), PDF pp. 2–4 and 7.

**Boundary:** a set of picks is not yet an event catalog; [phase-association](phase-association.md) must connect observations across stations.
