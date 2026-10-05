---
type: source
title: "InSARHub v0.4.2 documentation: installation, account setup, CLI workflows"
tags: ["seismic-processing"]
sources: ["insarhub-docs-v042-cli.md"]
related: ["insarhub","li-2026-insarhub"]
created: "2026-10-06"
updated: "2026-10-06"
authors: ["Jiawei Li","Sayyad Mohammad Javad Mirzadeh","Ryan Smith"]
year: 2026
venue: "Repository documentation (v0.4.2 docs/quickstart)"
url: "https://jldz9.github.io/InSARHub/"
source_file: "insarhub-docs-v042-cli.md"
original_filename: "docs/quickstart/*.md"
evidence_status: "local-primary-source"
---

# InSARHub v0.4.2 documentation

**Citation:** InSARHub documentation, v0.4.2 quickstart (install / account setup / CLI / running).

**Version note:** Version-matched to the vendored v0.4.2 source; four quickstart pages concatenated as logical pages 1–4.

## Document purpose

Operational reference for installing InSARHub, configuring free accounts (NASA Earthdata, Copernicus Data Space, Copernicus Climate Data Store) and driving the CLI workflows used by the `seismic-insar` skill.

## What to extract when implementing

1. Environment: Python 3.11–3.12, numpy<2.0, GDAL>=3.8 from conda-forge; the upstream `environment.yml` comments record two confirmed ABI traps (libgdal-netcdf floor; conda-not-pip rasterio/burst2safe) — do not simplify them (logical p. 1).
2. Credentials: `~/.netrc` entries for `urs.earthdata.nasa.gov` and `dataspace.copernicus.eu`; `~/.cdsapirc` for PyAPS tropospheric correction; all accounts free (logical p. 2).
3. CLI pattern: `insarhub downloader -N S1_SLC --AOI ... --start --end -w <dir> --select-pairs` → `insarhub processor -N Hyp3_S1 -w <dir> submit|refresh|download` → `insarhub analyzer -N Hyp3_Mintpy_SBAS -w <dir> run`; each command persists/reloads `<dir>/insarhub_config.json`, so changed parameters must be passed explicitly (logical p. 3–4).
4. The HyP3 cloud path needs no local SLC download; local engines add `--download -O` and heavier toolchains (logical p. 4).

## Scope and limitations

The docs describe upstream defaults for network-scale SBAS processing; they do not encode coseismic capture policy (per-event brackets, magnitude thresholds, HyP3 quota discipline) — those are this workflow's project rules in the stage skill.

## Relevance to this collection

Version-matched operating reference for the `insar` stage; method background in the [paper](li-2026-insarhub.md).

## Evidence and reading guide

- [Logical p. 1](../../raw/sources/insarhub-docs-v042-cli.md#page=1) — Installation and environment (ABI trap comments).
- [Logical p. 2](../../raw/sources/insarhub-docs-v042-cli.md#page=2) — Account setup: Earthdata / CDSE / CDS, netrc formats.
- [Logical p. 3](../../raw/sources/insarhub-docs-v042-cli.md#page=3) — CLI usage and per-engine command workflows.
- [Logical p. 4](../../raw/sources/insarhub-docs-v042-cli.md#page=4) — Running workflows; GUI/API alternatives.

- [Original markdown (cli)](../../raw/sources/insarhub-docs-v042-cli.md)
- [Page-anchored extracted text](../../raw/assets/extracted/insarhub-docs-v042.md)

## Connected knowledge

[insarhub](../entities/insarhub.md) · [li-2026-insarhub](li-2026-insarhub.md)
