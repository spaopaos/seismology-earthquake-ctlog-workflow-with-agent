---
type: comparison
title: "Roles of the Seismic Processing Methods"
tags: ["seismic-processing"]
sources: ["zhu-2019-phasenet.pdf","zhu-2022-gamma.pdf","klein-2002-hypoinverse.pdf","waldhauser-2001-hypodd.pdf","zhou-2022-palm.pdf"]
related: ["catalog-construction","phase-picking","phase-association","absolute-location","double-difference-relocation","matched-filter-detection"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Roles of the Seismic Processing Methods

| Method | Principal input | Principal output | Main question |
|---|---|---|---|
| PhaseNet | Three-component waveforms | P/S picks and scores | When did a phase arrive at this station? |
| GaMMA | Network picks and station/model information | Event hypotheses and pick assignments | Which arrivals belong to the same earthquake? |
| HYPOINVERSE | Associated phases, stations, velocity model | Absolute locations and origin times | Where and when did the earthquake occur? |
| HypoDD/ph2dt | Initial catalog and linked differential times | Relative relocation and diagnostics | How are neighboring events positioned relative to one another? |
| MESS | Templates and continuous waveforms | Additional detections and correlated timing | Which signals resemble known events across stations? |

These methods address different stages. They are not substitutes that can be ranked using one common metric. PALM already combines several stages but uses its own initial picker and associator.

**Grounding:** [zhu-2019-phasenet](../sources/zhu-2019-phasenet.md); [zhu-2022-gamma](../sources/zhu-2022-gamma.md); [klein-2002-hypoinverse](../sources/klein-2002-hypoinverse.md); [waldhauser-2001-hypodd](../sources/waldhauser-2001-hypodd.md); [zhou-2022-palm](../sources/zhou-2022-palm.md). Each source page provides PDF-page references and version details.
