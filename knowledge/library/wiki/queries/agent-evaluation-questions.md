---
type: query
title: "How Should a Seismology Agent Be Evaluated?"
tags: ["scientific-agents","seismic-processing"]
sources: ["zhou-2024-autoba.pdf","zhang-2025-geoscience-workflow.pdf","ren-2025-seismology-modeling-agent.pdf","waldhauser-2001-hypodd.pdf"]
related: ["research-agent-design-lessons","scientific-agent-comparison","uncertainty-and-quality-control"]
created: "2026-09-14"
updated: "2026-09-14"
status: "open"
---

# How Should a Seismology Agent Be Evaluated?

## Proposed evaluation questions

1. Can the agent complete each processing stage with valid, traceable artifacts?
2. Do results match a trusted workflow under the same data and parameters?
3. Which failures are recovered by automated repair, and which require a scientific decision?
4. Do repeated runs preserve the same inputs, effective parameters, and conclusions?
5. Are catalog quality and relocation stability preserved when execution is automated?

These are proposed research questions. The local papers motivate them but do not provide an end-to-end benchmark for a seismic catalog agent. AutoBA's stage-specific results and HypoDD's robustness guidance are particularly relevant starting points.
