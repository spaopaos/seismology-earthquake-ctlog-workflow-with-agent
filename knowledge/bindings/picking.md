# Picking — execution binding

The 2019 source describes original PhaseNet. PhaseNet+ polarity outputs, reader behavior and checkpoint identity must use the pinned EQNet implementation and release wrapper.

## Read in this order

1. The current stage skill and this version binding.
2. Relevant Wiki pages for explanation and context.
3. The pinned source/manual for implementation-specific numbers, fields or units.
4. Current data calculations/trials and actual effective configuration for decisions.

## Current implementation evidence

- [workflow_policy](../../skills/seismic-picking/SKILL.md)
- [pinned_implementation](../../knowledge/repos/EQNet/predict.py)
- [checked_reader_and_local_checkpoint](../../skills/seismic-picking/scripts/eqnet_pick.py)
- [implementation_notes](../../skills/seismic-picking/references/EQNET_FACTS.md)

## Wiki reading route

- [PhaseNet](../library/wiki/entities/phasenet.md)
- [PhaseNet: a deep-neural-network-based seismic arrival-time picking method](../library/wiki/sources/zhu-2019-phasenet.md)
- [Seismic Phase Picking](../library/wiki/concepts/phase-picking.md)
- [Version and Evidence Gaps](../library/wiki/queries/version-and-evidence-gaps.md)

The original Wiki records its eight-source scope. These bindings add execution context; they do not claim independent scientific validation of every Wiki statement.
