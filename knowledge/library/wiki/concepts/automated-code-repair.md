---
type: concept
title: "Automated Code Repair in Scientific Workflows"
tags: ["scientific-agents"]
sources: ["zhou-2024-autoba.pdf"]
related: ["autoba","agent-orchestration","uncertainty-and-quality-control"]
created: "2026-09-14"
updated: "2026-09-14"
---

# Automated Code Repair in Scientific Workflows

Automated code repair feeds execution failures back into a model so it can revise generated commands or code. In AutoBA, ACR is evaluated separately from planning and code generation.

On the reported 40-case suite, end-to-end successes increase from 26 to 35 with ACR, while successful plans remain 36 in both settings ([zhou-2024-autoba](../sources/zhou-2024-autoba.md), PDF p. 10). This separates the contribution of execution recovery from the ability to propose a workflow.

The discussion identifies tool packaging and entry-point problems among failure sources (PDF p. 12). Repair mechanisms should therefore preserve the original error and the exact change that resolved it.

**Synthesis for seismology:** a rerun that completes must still be checked for units, event IDs, time conventions, phase assignments, and plausible scientific output. These seismic checks are proposed transfer criteria, not experiments reported by AutoBA.
