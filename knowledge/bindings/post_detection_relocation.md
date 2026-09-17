# Post-MESS joint relocation — execution binding

The current maintained stage is joint lite: the MESS-native dt.cc together with the first-round medium-tier ph2dt dt.ct reused verbatim, IDAT=3. It produces exactly three independent CC-threshold catalogs. DAMP selection uses the same spatial-evidence rule as first-round relocation, with new trials for each detection tier.

Read the stage skill, the shared damping rule, the 2001 HypoDD manual (physical PDF pages 6, 9, 13, 18–20), and the maintained converters/runner. The manual documents common origin-time references, DT=T1−T2, OTC, joint link thresholds and weighting. It is not proof of the exact pinned binary's source/build identity; that provenance limitation remains.

The joint iteration schedule, the OBSCC+OBSCT effective link threshold and the three CC products are explicit project starting settings, not universal paper-derived optima. The reused CT bundle is hash-tied to the first-round solver evidence and is never rewritten; newly detected events connect to the catalog network only through MESS cross-correlation links to their templates. Upstream ERH is only a declared comparison scale for MESS events.

- [Stage policy](../../skills/seismic-post-detection-relocation/SKILL.md)
- [Shared DAMP rule](../../skills/seismic-relocation/references/damping.md)
- [Input preparation](../../skills/seismic-post-detection-relocation/scripts/prepare_inputs.py)
- [Independent source verifier](../../skills/seismic-post-detection-relocation/scripts/verify_inputs.py)
- [Native CC/CT validation](../../contracts/hypodd_inputs.py)
- [Joint runner](../../skills/seismic-relocation/scripts/run_hypodd.py)
- [Stage orchestration](../../skills/seismic-post-detection-relocation/scripts/run_stage.py)

Original Wiki pages and PDFs are unchanged. New execution bindings belong to this workflow revision; old analyses retain their original knowledge locks.
