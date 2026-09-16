---
type: concept
title: "Scientific Agent Orchestration"
tags: ["scientific-agents"]
sources: ["zhou-2024-autoba.pdf","zhang-2025-geoscience-workflow.pdf","ren-2025-seismology-modeling-agent.pdf"]
related: ["autoba","mindat-agent-workflow","specfem-mcp","scientific-agent-comparison"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Scientific Agent Orchestration

Scientific agent orchestration translates a research request into tool use, execution, inspection, and further action. The LLM's role and the tools' responsibilities differ substantially among the three agent papers.

- [autoba](../entities/autoba.md) emphasizes dynamic analysis plans, generated code, execution feedback, and repair.
- [mindat-agent-workflow](../entities/mindat-agent-workflow.md) routes among predefined collectors and plotters.
- [specfem-mcp](../entities/specfem-mcp.md) exposes an established simulation suite through structured server tools.

These papers support making execution outcomes visible to the orchestrator. They provide different levels of quantitative evidence and do not establish a universal superiority of multi-agent over single-agent architectures.

**Synthesis:** separate the assessment of a plan, the success of tool execution, and the scientific validity of the output. A valid JSON call or a zero exit code is useful evidence at only one of those levels.

**Evidence:** [zhou-2024-autoba](../sources/zhou-2024-autoba.md), PDF pp. 10, 12; [zhang-2025-geoscience-workflow](../sources/zhang-2025-geoscience-workflow.md), PDF pp. 3–4, 7–8; [ren-2025-seismology-modeling-agent](../sources/ren-2025-seismology-modeling-agent.md), PDF pp. 8, 22, 24.
