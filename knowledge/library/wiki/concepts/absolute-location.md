---
type: concept
title: "Absolute Earthquake Location"
tags: ["seismic-processing"]
sources: ["klein-2002-hypoinverse.pdf","waldhauser-2001-hypodd.pdf","zhou-2022-palm.pdf"]
related: ["hypoinverse","double-difference-relocation","uncertainty-and-quality-control"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Absolute Earthquake Location

Absolute location estimates an earthquake's hypocenter and origin time with respect to a geographic reference and Earth model. Observed arrivals are compared with predicted travel times, and source parameters are adjusted to improve agreement.

The quality of the result depends on station distribution, pick errors, phase identification, model error, weighting, and starting assumptions. Small residuals can coexist with uncertain depth or a systematically shifted source.

[hypoinverse](../entities/hypoinverse.md) documents velocity models, input conventions, weighting, location output, and conditional uncertainty information. [hypodd](../entities/hypodd.md) subsequently emphasizes how relative constraints can sharpen internal geometry while leaving cluster position uncertain.

**Evidence:** [klein-2002-hypoinverse](../sources/klein-2002-hypoinverse.md), PDF pp. 5–8 and 112–113; [waldhauser-2001-hypodd](../sources/waldhauser-2001-hypodd.md), PDF pp. 3 and 9; [zhou-2022-palm](../sources/zhou-2022-palm.md), PDF pp. 6 and 10.
