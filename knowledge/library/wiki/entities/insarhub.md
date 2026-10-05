---
type: entity
title: "InSARHub"
tags: ["seismic-processing"]
sources: ["li-2026-insarhub.md","insarhub-docs-v042-cli.md"]
related: ["li-2026-insarhub","insarhub-docs-v042","uncertainty-and-quality-control","version-and-evidence-gaps"]
created: "2026-10-06"
updated: "2026-10-06"
---

# InSARHub

InSARHub is a modular Python framework (MIT) automating the full InSAR chain: satellite scene search and download, interferogram generation, and SBAS time-series analysis, driven by one shared `insarhub_config.json` through a CLI, a Python API, or a self-hosted web GUI ([li-2026-insarhub](../sources/li-2026-insarhub.md)).

**Three plugin modules** — `downloader` (ASF Sentinel-1 SLC/burst, NISAR; baseline networks with pair quality scoring from snow cover, precipitation, NDVI and land cover), `processor` (cloud HyP3/GAMMA, or local ISCE2/GMTSAR/ISCE3 via Docker or SLURM), `analyzer` (MintPy SBAS, GMTSAR SBAS, dolphin phase linking). Jobs are tracked uniformly across cloud and HPC backends with resumable state ([docs](../sources/insarhub-docs-v042.md), logical p. 3).

In this workflow collection, InSARHub supplies the `insar` stage: coseismic deformation capture for relocated catalog events above a magnitude threshold. Execution uses the vendored v0.4.2 with the HyP3 cloud path (`Hyp3_S1`); no local SAR toolchain is required for that path, but a dedicated conda environment (Python 3.11–3.12, numpy<2.0, GDAL>=3.8) is mandatory — see [version-and-evidence-gaps](../queries/version-and-evidence-gaps.md).

Coseismic capture is per-event: a clean interferometric pair must bracket the target event alone, inside its bracket window; pairs spanning two threshold events carry both signals. Sentinel-1's 12-day revisit bounds what can be separated.
