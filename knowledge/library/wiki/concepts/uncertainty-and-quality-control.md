---
type: concept
title: "Uncertainty and Quality Control"
tags: ["seismic-processing"]
sources: ["zhu-2019-phasenet.pdf","zhu-2022-gamma.pdf","klein-2002-hypoinverse.pdf","waldhauser-2001-hypodd.pdf","zhou-2022-palm.pdf"]
related: ["absolute-location","double-difference-relocation","catalog-construction"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Uncertainty and Quality Control

Quality control must follow the specific scientific quantity produced at each stage.

| Stage | Evidence to examine | Interpretation to avoid |
|---|---|---|
| Picking | Phase errors, timing residuals, noise behavior | Treating a model score as a calibrated timing uncertainty |
| Association | Event coherence, phase support, unassigned picks, model mismatch | Treating every grouped pick set as a confirmed event |
| Absolute location | Residuals, geometry, depth sensitivity, model assumptions | Equating a small RMS with absolute accuracy |
| Relative relocation | Pair connectivity, structural stability, centroid shifts, retention | Equating a tight cluster with a known absolute position |
| Matched filtering | Template coverage, duplicate handling, threshold sensitivity | Equating larger event counts with higher reliability |

This table is a synthesis across the local sources. The strongest explicit robustness guidance is in the hypoDD manual: examine damping and geometry, test sensitivity, and use SVD on subsets to assess LSQR uncertainty (PDF pp. 9, 13).

**Evidence:** [zhu-2019-phasenet](../sources/zhu-2019-phasenet.md), PDF pp. 4, 11; [zhu-2022-gamma](../sources/zhu-2022-gamma.md), PDF pp. 3–5; [klein-2002-hypoinverse](../sources/klein-2002-hypoinverse.md), PDF pp. 112–113; [waldhauser-2001-hypodd](../sources/waldhauser-2001-hypodd.md), PDF pp. 9, 13; [zhou-2022-palm](../sources/zhou-2022-palm.md), PDF pp. 8–10.
