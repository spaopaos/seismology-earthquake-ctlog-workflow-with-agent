---
type: source
title: "Earthquake Phase Association Using a Bayesian Gaussian Mixture Model"
tags: ["seismic-processing"]
sources: ["zhu-2022-gamma.pdf"]
related: ["gamma","phase-association","catalog-construction","uncertainty-and-quality-control"]
created: "2026-09-14"
updated: "2026-09-14"
authors: ["Weiqiang Zhu","Ian W. McBrearty","S. Mostafa Mousavi","William L. Ellsworth","Gregory C. Beroza"]
year: 2022
venue: "Journal of Geophysical Research: Solid Earth 127, e2021JB023249"
url: "https://doi.org/10.1029/2021JB023249"
source_file: "zhu-2022-gamma.pdf"
original_filename: "JGR Solid Earth - 2022 - Zhu - Earthquake Phase Association Using a Bayesian Gaussian Mixture Model.pdf"
evidence_status: "local-primary-source"
---

# Earthquake Phase Association Using a Bayesian Gaussian Mixture Model

**Citation:** Weiqiang Zhu; Ian W. McBrearty; S. Mostafa Mousavi; William L. Ellsworth; Gregory C. Beroza (2022). Journal of Geophysical Research: Solid Earth 127, e2021JB023249. DOI: 10.1029/2021JB023249.

**Version note:** Journal article.

## Research problem

Dense pick streams must be grouped into earthquake events, including during sequences that overlap in time and space. GaMMA formulates this as an unsupervised mixture-model problem with earthquake physics constraining each cluster.

## Method

Each mixture component represents an event. Expected arrivals depend on event origin time, location, station geometry, and travel times; expected amplitudes depend on event magnitude and source–station distance. Gaussian residual distributions represent the fit between observations and these predictions. The Bayesian formulation regularizes mixture weights and addresses the unknown number of events.

Expectation–maximization alternates between probabilistic phase assignments and updates of event parameters. Arrival times and optional amplitudes provide complementary information: picks close in time can still be separated when their station-dependent timing and amplitudes favor different source hypotheses.

## Evidence

The authors evaluate synthetic phase sets and the 2019 Ridgecrest sequence. They report effective association in dense sequences and useful initial source estimates. The paper's examples test robustness to pick errors, false picks, and closely spaced events. Numerical case-study results remain tied to their data, velocity assumptions, and evaluation choices.

## Scope and limitations

Association depends on the consistency of station metadata, phase types, arrival times, and the travel-time model. If amplitudes are supplied, their definition and units must match the amplitude model. The proof-of-concept treatment includes simplified velocity assumptions. Association-stage locations and magnitudes require downstream validation; they should not automatically be treated as a final relocated or calibrated catalog.

The supplied paper does not establish a universal DBSCAN time window for every network. Any implementation-specific preprocessing or parameter default must be checked against the software version and target data.

## Relevance to this collection

GaMMA connects [phasenet](../entities/phasenet.md) picks to subsequent [hypoinverse](../entities/hypoinverse.md) location. Using it in place of PAL's native associator is a cross-paper workflow composition, not a verbatim reproduction of the original PALM architecture.

## Evidence and reading guide

- [PDF p. 1](../../raw/sources/zhu-2022-gamma.pdf#page=1) — Abstract and stated contribution.
- [PDF p. 3](../../raw/sources/zhu-2022-gamma.pdf#page=3) — Mixture formulation and Bayesian treatment of event counts.
- [PDF p. 4](../../raw/sources/zhu-2022-gamma.pdf#page=4) — Parameter estimation and event responsibilities.
- [PDF p. 5](../../raw/sources/zhu-2022-gamma.pdf#page=5) — Travel-time and amplitude modeling assumptions.
- [PDF p. 10](../../raw/sources/zhu-2022-gamma.pdf#page=10) — Ridgecrest analysis and discussion.
- [PDF p. 13](../../raw/sources/zhu-2022-gamma.pdf#page=13) — Conclusions and availability statements.

- [Original PDF](../../raw/sources/zhu-2022-gamma.pdf)
- [Complete page-numbered extracted text](../../raw/assets/extracted/zhu-2022-gamma.md)

## Connected knowledge

[gamma](../entities/gamma.md) · [phase-association](../concepts/phase-association.md) · [catalog-construction](../synthesis/catalog-construction.md) · [uncertainty-and-quality-control](../concepts/uncertainty-and-quality-control.md)
