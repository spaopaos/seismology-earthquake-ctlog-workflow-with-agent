---
type: synthesis
title: "From Waveforms to an Expanded Earthquake Catalog"
tags: ["seismic-processing"]
sources: ["zhu-2019-phasenet.pdf","zhu-2022-gamma.pdf","klein-2002-hypoinverse.pdf","waldhauser-2001-hypodd.pdf","zhou-2022-palm.pdf"]
related: ["seismic-method-comparison","phasenet","gamma","hypoinverse","hypodd","palm-mess","uncertainty-and-quality-control"]
created: "2026-09-14"
updated: "2026-09-14"
---

# From Waveforms to an Expanded Earthquake Catalog

This page proposes a conceptual composition of the local papers. It is not a claim that the combined pipeline has been implemented or validated here.

1. Prepare waveform and station metadata with explicit timing, units, components, and coverage.
2. Use [phasenet](../entities/phasenet.md) or another validated picker to obtain station arrivals.
3. Use [gamma](../entities/gamma.md) to associate arrivals into event hypotheses.
4. Use [hypoinverse](../entities/hypoinverse.md) with a justified velocity model to obtain absolute locations.
5. Use [hypodd](../entities/hypodd.md) to refine relative geometry, keeping uncertainty and centroid diagnostics.
6. Build suitable templates and use [palm-mess](../entities/palm-mess.md) to scan for additional detections.
7. Associate duplicate template detections and assess correlated timing before any further relocation.

The original PALM paper demonstrates a related complete architecture, but its initial picker and associator differ from steps 2 and 3 above. That distinction must remain explicit in a methods section.

At each transition, preserve event and pick identity, observations retained or rejected, model assumptions, and provenance. Successful file conversion should be followed by [uncertainty-and-quality-control](../concepts/uncertainty-and-quality-control.md) for the scientific product.

**Supporting literature:** the five source pages linked by [seismic-method-comparison](../comparisons/seismic-method-comparison.md). Operational defaults, binary versions, and acceptance criteria for a particular dataset remain to be justified; see [version-and-evidence-gaps](../queries/version-and-evidence-gaps.md).
