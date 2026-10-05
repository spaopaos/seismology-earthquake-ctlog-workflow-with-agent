# Post-MESS joint relocation — execution binding

The current maintained stage is joint lite (Eryuan rules): the MESS-native dt.cc together with the first-round medium-tier ph2dt dt.ct reused verbatim, IDAT=3, OBSCC=4/OBSCT=6, producing one joint catalog covering template events and MESS new detections. DAMP selection uses the same spatial-evidence rule as first-round relocation, via the parallel scan mode of the joint runner.

Read the stage skill, the shared damping rule, and the 2001 HypoDD manual (physical PDF pages 6, 9, 13, 18–20). The manual documents common origin-time references, DT=T1−T2, OTC, joint link thresholds and weighting. It is not proof of the exact pinned binary's source/build identity; that provenance limitation remains.

The joint iteration schedule, the OBSCC+OBSCT effective link threshold and the single joint catalog are explicit project starting settings, not universal paper-derived optima. The reused CT bundle is never rewritten; newly detected events connect to the catalog network only through MESS cross-correlation links to their templates. Upstream ERH is only a declared comparison scale for MESS events.

- [Stage policy](../../skills/seismic-post-detection-relocation/SKILL.md)
- [Shared DAMP rule](../../skills/seismic-relocation/references/damping.md)
- [Joint input builder](../../skills/seismic-post-detection-relocation/scripts/4_build_joint_inputs.py)
- [Joint solver + DAMP scan](../../skills/seismic-post-detection-relocation/scripts/5_run_hypodd_joint.py)
- [Joint catalog parser](../../skills/seismic-post-detection-relocation/scripts/6_parse_joint.py)
- [Initial settings](../../../configs/pipeline.example.json)

Original Wiki pages and PDFs are unchanged. New execution bindings belong to this workflow revision; old analyses retain their original knowledge locks.
