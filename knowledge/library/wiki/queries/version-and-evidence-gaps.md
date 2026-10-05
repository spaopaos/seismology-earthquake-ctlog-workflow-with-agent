---
type: query
title: "Version and Evidence Gaps"
tags: ["seismic-processing","scientific-agents"]
sources: ["zhu-2019-phasenet.pdf","klein-2002-hypoinverse.pdf","waldhauser-2001-hypodd.pdf","zhou-2022-palm.pdf","skousmal-2024-skhash.pdf","skhash-manual-v1.1.pdf","ren-2025-seismology-modeling-agent.pdf"]
related: ["phasenet","hypoinverse","hypodd","palm-mess","skhash","specfem-mcp"]
created: "2026-09-14"
updated: "2026-10-06"
status: "open"
---

# Version and Evidence Gaps

## Open questions

- Which primary source and software revision document the exact PhaseNet+ model and polarity outputs used in a future workflow? The local paper covers original PhaseNet.
- Which version-matched manual and format specification should accompany HYPOINVERSE 1.40? The local guide covers April 2002 HYPOINVERSE-2000.
- Which HypoDD distribution and parameter semantics are intended for execution? The local manual is version 1.0 from 2001.
- How should MESS thresholds and template selection be validated on the target network? The local paper reports one Ridgecrest application.
- Are there later versions of the SPECFEM agent preprint with additional validation? Only arXiv v1 is represented here.

These gaps are intentionally retained. No additional papers or missing benchmark results were invented during curation.

## Addendum (2026-10-06 revision)

The focal-mechanism stage is an exception to the version-gap pattern above: its paper (skousmal-2024-skhash) and a version-matched v1.1 manual (skhash-manual-v1.1) are both in this corpus, and execution uses the vendored v1.1 source with four behavior-preserving compatibility patches recorded in `knowledge/repos/SKHASH/VENDORED_PATCHES.md`. The remaining open question for this stage is empirical, not documentary: how machine-learning polarity-score thresholds and reversal lists should be validated for a new network is decided per run, not by the manual.
