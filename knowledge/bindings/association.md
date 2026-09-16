# Association — execution binding

The paper explains association assumptions. The current code establishes linear m/s amplitude input and estimate_eps behavior; project rules recommend 10 seconds and preserve the user choice. Search depth and projected margins are explicit regional configuration.

## Read in this order

1. The current stage skill and this version binding.
2. Relevant Wiki pages for explanation and context.
3. The pinned source/manual for implementation-specific numbers, fields or units.
4. Current data calculations/trials and actual effective configuration for decisions.

## Current implementation evidence

- [workflow_policy](../../skills/seismic-association/SKILL.md)
- [pinned_implementation](../../knowledge/repos/GAMMA/gamma/utils.py)
- [parameter_calculation](../../skills/seismic-association/scripts/prepare_dbscan_eps.py)
- [actual_configuration](../../skills/seismic-association/scripts/run_gamma.py)
- [implementation_notes](../../skills/seismic-association/references/GAMMA_FACTS.md)

## Wiki reading route

- [GaMMA](../library/wiki/entities/gamma.md)
- [Earthquake Phase Association Using a Bayesian Gaussian Mixture Model](../library/wiki/sources/zhu-2022-gamma.md)
- [Earthquake Phase Association](../library/wiki/concepts/phase-association.md)
- [Uncertainty and Quality Control](../library/wiki/concepts/uncertainty-and-quality-control.md)

The original Wiki records its eight-source scope. These bindings add execution context; they do not claim independent scientific validation of every Wiki statement.
