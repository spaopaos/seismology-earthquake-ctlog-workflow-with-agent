---
type: source
title: "InSARHub: A Modular Python Framework for Automated InSAR and Time-Series Processing with a Built-in Web GUI"
tags: ["seismic-processing"]
sources: ["li-2026-insarhub.md"]
related: ["insarhub","insarhub-docs-v042","version-and-evidence-gaps"]
created: "2026-10-06"
updated: "2026-10-06"
authors: ["Jiawei Li","Sayyed Mohammad Javad Mirzadeh","Ryan Smith"]
year: 2026
venue: "Journal of Open Source Software (software DOI 10.5281/zenodo.20190966)"
url: "https://github.com/jldz9/InSARHub"
source_file: "li-2026-insarhub.md"
original_filename: "paper.md"
evidence_status: "local-primary-source"
---

# InSARHub: A Modular Python Framework for Automated InSAR and Time-Series Processing with a Built-in Web GUI

**Citation:** Jiawei Li; Sayyed Mohammad Javad Mirzadeh; Ryan Smith (2026). Journal of Open Source Software; software DOI 10.5281/zenodo.20190966.

**Version note:** JOSS-style markdown paper included in the v0.4.2 repository; the vendored software version matches.

## Research problem

Existing InSAR tools each cover one segment (ISCE2/ISCE3 interferograms, HyP3 cloud processing, MintPy time series, LiCSBAS, ARIA-tools, MiaplPy/Dolphin), and chaining them manually is expert work. InSARHub treats them as interchangeable backends behind a plugin registry with three core modules — Downloader, Processor, Analyzer — plus a unified job manager.

## Method highlights

- Shared configuration across GUI/CLI/API; workflows move between interfaces without conversion.
- Graph-based pair selection with baseline constraints and quality scoring using snow cover, precipitation, NDVI and land-cover type; an interactive network editor in the GUI.
- Job tracking across cloud (HyP3/ASF) and SLURM HPC backends, per-job status, retry-from-failure, resumable workflows.
- Demonstrated throughput: three 10-year Sentinel-1 tracks processed in under a month (US Army ERDC groundwater project), against an estimated 1–2 months of manual expert effort per equivalent.

## Scope and limitations

The paper is software engineering, not a detection-threshold study: it does not establish what magnitude of earthquake is detectable by InSAR in a given region — that depends on magnitude, depth, mechanism, vegetation/season and atmosphere, and must be judged per case. Pair quality scores are heuristics for network building, not coseismic-bracketing logic; catalog-driven coseismic capture (per-event bracket windows) is this workflow's own project rule.

## Relevance to this collection

InSARHub supplies the `insar` stage: search/pair/process/analyze wrapped by the `seismic-insar` skill launchers. Operating detail is version-matched in the [v0.4.2 docs](insarhub-docs-v042.md).

## Evidence and reading guide

- [Logical p. 1](../../raw/sources/li-2026-insarhub.md#page=1) — Full paper: architecture, plugins, job manager, GUI, throughput evidence.

- [Original markdown](../../raw/sources/li-2026-insarhub.md)
- [Page-anchored extracted text](../../raw/assets/extracted/li-2026-insarhub.md)

## Connected knowledge

[insarhub](../entities/insarhub.md) · [insarhub-docs-v042](insarhub-docs-v042.md) · [version-and-evidence-gaps](../queries/version-and-evidence-gaps.md)
