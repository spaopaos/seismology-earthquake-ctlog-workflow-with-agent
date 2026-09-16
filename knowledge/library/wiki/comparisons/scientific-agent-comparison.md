---
type: comparison
title: "Comparison of Scientific Agent Architectures"
tags: ["scientific-agents"]
sources: ["zhou-2024-autoba.pdf","zhang-2025-geoscience-workflow.pdf","ren-2025-seismology-modeling-agent.pdf"]
related: ["autoba","mindat-agent-workflow","specfem-mcp","research-agent-design-lessons"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Comparison of Scientific Agent Architectures

| Aspect | AutoBA | Mindat workflow | SPECFEM MCP suite |
|---|---|---|---|
| Domain | Conventional multi-omics | Mineral data retrieval and visualization | Seismic forward simulation |
| Main interface | Generated plans and executable code | Supervisor and four specialized tool agents | Schematized tools wrapping existing solvers |
| Execution feedback | Explicit automated repair | Results return to supervisor | Tool results and intermediate simulation artifacts |
| Demonstrated evidence | 40 cases; stage-specific success counts | Example networks and heatmaps | Five simulation case studies |
| Evidence boundary | Domain and model-specific benchmark | Broader quantitative evaluation proposed | Broader autonomous discovery proposed |
| Transferable lesson | Measure execution and recovery separately | Bound tool responsibilities and inspect arguments | Preserve trusted numerical executables behind clear interfaces |

The three evaluations are not directly comparable. A ranking by a single success rate would misrepresent the available evidence.

**Grounding:** [zhou-2024-autoba](../sources/zhou-2024-autoba.md), PDF pp. 10, 12; [zhang-2025-geoscience-workflow](../sources/zhang-2025-geoscience-workflow.md), PDF pp. 3–4, 7–8; [ren-2025-seismology-modeling-agent](../sources/ren-2025-seismology-modeling-agent.md), PDF pp. 8, 22, 24.

**Synthesis:** these designs offer complementary ideas for a seismic processing assistant. The papers do not show that combining all their features produces a better system.
