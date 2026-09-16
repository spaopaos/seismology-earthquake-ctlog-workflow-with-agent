---
type: concept
title: "Double-Difference Relocation"
tags: ["seismic-processing"]
sources: ["waldhauser-2001-hypodd.pdf","zhou-2022-palm.pdf"]
related: ["hypodd","absolute-location","uncertainty-and-quality-control"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Double-Difference Relocation

Double-difference relocation uses differences between event observations at common stations to constrain relative source positions. Nearby sources share much of their propagation path, so differencing reduces common path-model errors.

For events i and j observed at station k, the central residual compares the observed arrival difference with the predicted difference:

$$r_{ij,k}=(t^{obs}_{i,k}-t^{obs}_{j,k})-(t^{calc}_{i,k}-t^{calc}_{j,k}).$$

Here predicted arrivals include origin time and travel time. This equation is a compact restatement of the manual's method description, not a new derivation.

Catalog picks and cross-correlation differential times have different error properties. The inversion must account for data weights and the connectivity of the event-pair graph. A disconnected or weakly constrained event cannot be made reliable merely by increasing iteration count.

**Evidence:** [waldhauser-2001-hypodd](../sources/waldhauser-2001-hypodd.md), PDF pp. 3–4, 9, and 13; [zhou-2022-palm](../sources/zhou-2022-palm.md), PDF p. 7.

**Interpretation:** improved relative structure does not establish the absolute position of that structure.
