---
type: source
title: "User’s Guide to HYPOINVERSE-2000, a Fortran Program to Solve for Earthquake Locations and Magnitudes"
tags: ["seismic-processing"]
sources: ["klein-2002-hypoinverse.pdf"]
related: ["hypoinverse","absolute-location","uncertainty-and-quality-control","version-and-evidence-gaps"]
created: "2026-09-14"
updated: "2026-09-14"
authors: ["Fred W. Klein"]
year: 2002
venue: "USGS Open-File Report 02-171, version 1.0"
url: ""
source_file: "klein-2002-hypoinverse.pdf"
original_filename: "hyp2000-1.0.pdf"
evidence_status: "local-primary-source"
---

# User’s Guide to HYPOINVERSE-2000, a Fortran Program to Solve for Earthquake Locations and Magnitudes

**Citation:** Fred W. Klein (2002). USGS Open-File Report 02-171, version 1.0. 

**Version note:** April 2002 program manual; not a manual for HYPOINVERSE 1.40.

## Document purpose

This is a software user's guide for HYPOINVERSE-2000, covering earthquake location, magnitude calculations, station and phase input, velocity models, command configuration, and output formats. It is an operational reference rather than a comparative machine-learning study.

## Core workflow

The program combines associated arrival observations, station information, an Earth velocity model, and location controls to estimate earthquake hypocenters and origin times. The manual supports multiple model configurations and describes layered and gradient structures, station delays, distance and residual weighting, and location-quality information.

Its outputs include summary catalogs, detailed print output, and archive records. The exact record layout and command behavior are integral to successful integration. The manual also covers duration- and amplitude-related magnitude procedures, which require the appropriate measurements and calibration.

## What to extract when implementing

1. Match the phase-input and station formats to the program version.
2. Record velocity-model and coordinate/depth conventions explicitly.
3. Track observation weights, rejected phases, residuals, and geometric coverage.
4. Preserve detailed output alongside the summary location catalog.
5. Treat magnitude computation as a separately justified calculation.

## Scope and limitations

Absolute locations depend on the velocity model and network geometry. A small travel-time residual alone does not establish accurate depth or correct geological interpretation. The manual's formal location uncertainties remain conditional on the chosen model and observations.

The supplied PDF identifies an April 2002 program version. Its formats and commands should not be assumed to be an exact specification for HYPOINVERSE 1.40. That version gap is recorded in [version-and-evidence-gaps](../queries/version-and-evidence-gaps.md).

## Relevance to this collection

HYPOINVERSE provides the absolute-location stage in [catalog-construction](../synthesis/catalog-construction.md), while [hypodd](../entities/hypodd.md) subsequently refines relative event geometry using differential observations.

## Evidence and reading guide

- [PDF p. 1](../../raw/sources/klein-2002-hypoinverse.pdf#page=1) — Version and report identity.
- [PDF p. 2](../../raw/sources/klein-2002-hypoinverse.pdf#page=2) — Contents: velocity models, weighting, and magnitude sections.
- [PDF p. 5](../../raw/sources/klein-2002-hypoinverse.pdf#page=5) — Program introduction and capabilities.
- [PDF p. 8](../../raw/sources/klein-2002-hypoinverse.pdf#page=8) — Crustal velocity models.
- [PDF p. 112](../../raw/sources/klein-2002-hypoinverse.pdf#page=112) — Eigenvalues, covariance output, and the error model.
- [PDF p. 113](../../raw/sources/klein-2002-hypoinverse.pdf#page=113) — Error ellipsoid interpretation and its limitations.

- [Original PDF](../../raw/sources/klein-2002-hypoinverse.pdf)
- [Complete page-numbered extracted text](../../raw/assets/extracted/klein-2002-hypoinverse.md)

## Connected knowledge

[hypoinverse](../entities/hypoinverse.md) · [absolute-location](../concepts/absolute-location.md) · [uncertainty-and-quality-control](../concepts/uncertainty-and-quality-control.md) · [version-and-evidence-gaps](../queries/version-and-evidence-gaps.md)
