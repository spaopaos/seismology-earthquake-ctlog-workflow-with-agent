---
type: entity
title: "HypoDD and ph2dt"
tags: ["seismic-processing"]
sources: ["waldhauser-2001-hypodd.pdf","zhou-2022-palm.pdf"]
related: ["waldhauser-2001-hypodd","double-difference-relocation","hypoinverse"]
created: "2026-09-14"
updated: "2026-09-14"
---

# HypoDD and ph2dt

ph2dt prepares event-pair observations from phase catalogs; HypoDD estimates relative hypocenter adjustments using differential travel times. Catalog-derived and cross-correlation-derived differential measurements can both be used.

**Input:** initial event locations, station coordinates, linked differential observations, velocity model, and inversion controls. **Output:** relocated events and diagnostics for residuals, adjustment size, event retention, centroid shift, and conditioning.

The manual's empirical damping guidance is subordinate to the observed stability of the solution ([waldhauser-2001-hypodd](../sources/waldhauser-2001-hypodd.md), PDF pp. 9, 13). A sharp-looking cluster can still have an uncertain absolute position.

PALM's MESS example uses correlation-derived differential times for relocation ([zhou-2022-palm](../sources/zhou-2022-palm.md), PDF p. 7). This differs from a catalog-only HypoDD run.
