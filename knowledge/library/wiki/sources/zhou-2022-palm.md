---
type: source
title: "An Earthquake Detection and Location Architecture for Continuous Seismograms: Phase Picking, Association, Location, and Matched Filter (PALM)"
tags: ["seismic-processing"]
sources: ["zhou-2022-palm.pdf"]
related: ["palm-mess","matched-filter-detection","catalog-construction","uncertainty-and-quality-control"]
created: "2026-09-14"
updated: "2026-09-14"
authors: ["Yijian Zhou","Han Yue","Lihua Fang","Shiyong Zhou","Li Zhao","Abhijit Ghosh"]
year: 2022
venue: "Seismological Research Letters 93(1), 413–425"
url: "https://doi.org/10.1785/0220210111"
source_file: "zhou-2022-palm.pdf"
original_filename: "palm.pdf"
evidence_status: "local-primary-source"
---

# An Earthquake Detection and Location Architecture for Continuous Seismograms: Phase Picking, Association, Location, and Matched Filter (PALM)

**Citation:** Yijian Zhou; Han Yue; Lihua Fang; Shiyong Zhou; Li Zhao; Abhijit Ghosh (2022). Seismological Research Letters 93(1), 413–425. DOI: 10.1785/0220210111.

**Version note:** January 2022 issue; the supplied PDF recommends a 2021 online-publication citation.

## Research problem

PALM builds an earthquake catalog from continuous seismograms, then increases detection coverage using internally obtained templates. It connects picking, association, location, relocation, and matched filtering into a complete workflow.

## Architecture

The initial PAL module combines STA/LTA and kurtosis-based picking, association, and location. The original study uses HYPOINVERSE for absolute locations and HypoDD for relocation. This initial catalog supplies templates for MESS: Match, Expand, Shift, and Stack.

MESS correlates templates with continuous data, expands correlation peaks to tolerate timing differences caused by source offsets, shifts station traces using template travel times, and stacks them to detect coherent events. Correlation-derived phase timing supports subsequent differential-time relocation.

## Case-study evidence

The study evaluates the early 2019 Ridgecrest aftershock sequence against SCSN and other published catalogs. It reports a relocated MESS catalog containing 59,159 events for its analyzed dataset and compares temporal behavior and fault structure with other catalogs. This count is specific to the paper's interval and settings.

Examples of Ridgecrest-specific settings include a 1 s expansion window and a 2 s origin-time grouping interval. The MESS relocation example requires detections supported by at least three templates and differential times from four stations. These values document the experiment and are not general defaults for a new network.

## Scope and limitations

Template coverage and initial location quality influence detection completeness and downstream geometry. Similar relative structures can coexist with differences in absolute depth. Correlation thresholds, duplicate merging, and minimum support change the resulting catalog.

The original PAL picker is not PhaseNet and its associator is not GaMMA. Combining those newer components with MESS is an adaptation. Likewise, the paper does not establish a universal three-tier CC policy of 0.4, 0.6, and 0.8.

## Relevance to this collection

PALM is the most direct reference for how the separate seismic methods can form a catalog-building workflow, while its exact original components must remain distinguishable from [catalog-construction](../synthesis/catalog-construction.md)'s proposed combination.

## Evidence and reading guide

- [PDF p. 1](../../raw/sources/zhou-2022-palm.pdf#page=1) — Abstract and bibliographic year ambiguity.
- [PDF p. 2](../../raw/sources/zhou-2022-palm.pdf#page=2) — Workflow overview.
- [PDF p. 6](../../raw/sources/zhou-2022-palm.pdf#page=6) — MESS correlation, expansion, shifting, and stacking.
- [PDF p. 7](../../raw/sources/zhou-2022-palm.pdf#page=7) — Correlation-derived timing and MESS relocation criteria.
- [PDF p. 8](../../raw/sources/zhou-2022-palm.pdf#page=8) — Published MESS event count and catalog comparison.
- [PDF p. 10](../../raw/sources/zhou-2022-palm.pdf#page=10) — Depth differences, relocation interpretation, and conclusions.

- [Original PDF](../../raw/sources/zhou-2022-palm.pdf)
- [Complete page-numbered extracted text](../../raw/assets/extracted/zhou-2022-palm.md)

## Connected knowledge

[palm-mess](../entities/palm-mess.md) · [matched-filter-detection](../concepts/matched-filter-detection.md) · [catalog-construction](../synthesis/catalog-construction.md) · [uncertainty-and-quality-control](../concepts/uncertainty-and-quality-control.md)
