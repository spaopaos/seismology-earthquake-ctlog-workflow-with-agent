---
type: source
title: "An AI Agent for Fully Automated Multi-Omic Analyses"
tags: ["scientific-agents"]
sources: ["zhou-2024-autoba.pdf"]
related: ["autoba","agent-orchestration","automated-code-repair","scientific-agent-comparison"]
created: "2026-09-14"
updated: "2026-09-14"
authors: ["Juexiao Zhou","Bin Zhang","Guowei Li","Xiuying Chen","Haoyang Li","Xiaopeng Xu","Siyuan Chen","Wenjia He","Chencheng Xu","Liwei Liu","Xin Gao"]
year: 2024
venue: "Advanced Science 11, 2407094"
url: "https://doi.org/10.1002/advs.202407094"
source_file: "zhou-2024-autoba.pdf"
original_filename: "Advanced Science - 2024 - Zhou - An AI Agent for Fully Automated Multi‐Omic Analyses.pdf"
evidence_status: "local-primary-source"
---

# An AI Agent for Fully Automated Multi-Omic Analyses

**Citation:** Juexiao Zhou; Bin Zhang; Guowei Li; Xiuying Chen; Haoyang Li; Xiaopeng Xu; Siyuan Chen; Wenjia He; Chencheng Xu; Liwei Liu; Xin Gao (2024). Advanced Science 11, 2407094. DOI: 10.1002/advs.202407094.

**Version note:** Journal article.

## Research problem

AutoBA targets end-to-end conventional multi-omics analysis from a small amount of user input: data locations, data descriptions, and an analysis goal. It addresses planning, tool acquisition, generated code, execution, and error repair.

## Method

An LLM plans an analysis and generates executable steps. Execution results and errors feed back into the process. The Automated Code Repair (ACR) component attempts to correct failures. The paper studies both online and local model backends, with different privacy and performance tradeoffs.

## Reported evidence

The evaluation covers 40 analysis cases across genomics, transcriptomics, proteomics, and metabolomics, with expert validation. Physical PDF p. 10 reports:

| Outcome | Without ACR | With ACR |
|---|---:|---:|
| Successful plans | 36/40 (90%) | 36/40 (90%) |
| Successful code/tool setup | 33/40 (82.5%) | 35/40 (87.5%) |
| Successful end-to-end analysis | 26/40 (65%) | 35/40 (87.5%) |

These are results from the paper's configuration and case set, not a guaranteed success rate for a different model or domain. The stage-specific breakdown shows why plausible plans are an inadequate substitute for successful execution.

## Scope and limitations

The discussion describes failures related to packages, unconventional tool entry points, configuration requirements, and limitations in tool knowledge. Forty cases cover only part of bioinformatics. Stronger execution robustness does not automatically establish the scientific validity of every analytical choice.

The results concern multi-omics, not seismology. Transferable ideas include explicit execution feedback, repair loops, provenance, and evaluation by stage. Their benefit for seismic processing would need direct experiments.

## Relevance to this collection

AutoBA provides a contrasting orchestration pattern to [mindat-agent-workflow](../entities/mindat-agent-workflow.md)'s predefined tools and [specfem-mcp](../entities/specfem-mcp.md)'s interfaces to existing numerical solvers.

## Evidence and reading guide

- [PDF p. 1](../../raw/sources/zhou-2024-autoba.pdf#page=1) — Problem, system purpose, and ACR motivation.
- [PDF p. 2](../../raw/sources/zhou-2024-autoba.pdf#page=2) — System design and workflow description.
- [PDF p. 9](../../raw/sources/zhou-2024-autoba.pdf#page=9) — Detailed case outcomes in Table 3.
- [PDF p. 10](../../raw/sources/zhou-2024-autoba.pdf#page=10) — Stage-specific success rates with and without ACR.
- [PDF p. 12](../../raw/sources/zhou-2024-autoba.pdf#page=12) — Comparisons, limitations, tool-selection bias, and reproducibility discussion.

- [Original PDF](../../raw/sources/zhou-2024-autoba.pdf)
- [Complete page-numbered extracted text](../../raw/assets/extracted/zhou-2024-autoba.md)

## Connected knowledge

[autoba](../entities/autoba.md) · [agent-orchestration](../concepts/agent-orchestration.md) · [automated-code-repair](../concepts/automated-code-repair.md) · [scientific-agent-comparison](../comparisons/scientific-agent-comparison.md)
