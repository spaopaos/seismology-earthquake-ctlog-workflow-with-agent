---
type: concept
title: "Scientific Tool Contracts and Provenance"
tags: ["scientific-agents"]
sources: ["zhang-2025-geoscience-workflow.pdf","ren-2025-seismology-modeling-agent.pdf","zhou-2024-autoba.pdf"]
related: ["mindat-agent-workflow","specfem-mcp","agent-orchestration","research-agent-design-lessons"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Scientific Tool Contracts and Provenance

A tool contract states what an operation accepts, what it produces, and how success or failure is observed. Provenance records the inputs, software, parameters, execution history, and resulting artifacts needed to interpret or repeat that operation.

The Mindat workflow uses structured arguments and tool-specific instructions. The SPECFEM suite exposes tool schemas and wraps configuration files and numerical executables. AutoBA exposes the separate stages at which an otherwise plausible workflow can fail.

**Cross-paper synthesis:** a scientific wrapper should preserve input identities, parameter values, software versions, output paths, and diagnostics. It should distinguish an execution error from an output that runs successfully but fails scientific quality checks.

The papers illustrate parts of this pattern. They do not demonstrate a complete shared provenance standard or a universal protocol that guarantees valid research.

**Evidence:** [zhang-2025-geoscience-workflow](../sources/zhang-2025-geoscience-workflow.md), PDF pp. 3–4, 7; [ren-2025-seismology-modeling-agent](../sources/ren-2025-seismology-modeling-agent.md), PDF pp. 7–8; [zhou-2024-autoba](../sources/zhou-2024-autoba.md), PDF pp. 10, 12.
