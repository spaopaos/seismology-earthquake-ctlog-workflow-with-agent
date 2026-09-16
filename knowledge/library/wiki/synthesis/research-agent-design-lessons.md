---
type: synthesis
title: "Design Lessons for a Seismology Research Agent"
tags: ["scientific-agents","seismic-processing"]
sources: ["zhou-2024-autoba.pdf","zhang-2025-geoscience-workflow.pdf","ren-2025-seismology-modeling-agent.pdf","waldhauser-2001-hypodd.pdf"]
related: ["scientific-agent-comparison","tool-contracts-and-provenance","agent-orchestration","agent-evaluation-questions"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Design Lessons for a Seismology Research Agent

The agent papers suggest three compatible design practices: expose bounded scientific operations, make execution results inspectable, and distinguish planning from successful completion. The hypoDD manual adds a complementary requirement: the result must survive scientific stability checks.

**Proposed application:** wrap existing seismic executables with explicit input/output contracts; preserve intermediate artifacts and diagnostics; make interpretation depend on quality checks appropriate to each stage. An execution repair loop should retain the reason for each change and re-evaluate the resulting science.

This is a synthesis recommendation, not an evaluated architecture. The collection supports components of the argument: AutoBA's repair comparison (PDF p. 10), Mindat's structured collectors and logs (PDF pp. 3, 7), SPECFEM's solver wrappers (PDF p. 8), and HypoDD's robustness requirements (PDF pp. 9, 13).

Measure workflow completion, reproducibility, and scientific validity separately. [agent-evaluation-questions](../queries/agent-evaluation-questions.md) records the experiments needed before stronger claims could be made.
