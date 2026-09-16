---
type: entity
title: "HYPOINVERSE"
tags: ["seismic-processing"]
sources: ["klein-2002-hypoinverse.pdf","zhou-2022-palm.pdf"]
related: ["klein-2002-hypoinverse","absolute-location","hypodd"]
created: "2026-09-14"
updated: "2026-09-14"
---

# HYPOINVERSE

HYPOINVERSE estimates absolute earthquake locations and origin times using associated phase arrivals, station information, and a velocity model. It also supports magnitude calculations when suitable measurements and calibration are provided.

**Input:** version-specific phase, station, model, and command files. **Output:** catalog summaries, detailed print records, and archive output. **Pipeline role:** absolute location before optional relative relocation.

The local reference is the April 2002 HYPOINVERSE-2000 manual ([klein-2002-hypoinverse](../sources/klein-2002-hypoinverse.md), PDF pp. 1, 5–8). PALM uses HYPOINVERSE as its absolute-location component ([zhou-2022-palm](../sources/zhou-2022-palm.md), PDF p. 6).

Version-specific format checks are necessary before applying this manual to a newer binary.
