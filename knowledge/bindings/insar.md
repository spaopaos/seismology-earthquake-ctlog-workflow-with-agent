# InSAR coseismic capture — execution binding

The paper is software background; the v0.4.2 docs are the version-matched
operating reference. Execution uses the vendored InSARHub v0.4.2 with the
HyP3 cloud path (Hyp3_S1, no local SAR toolchain) inside the dedicated
`insarhub` environment — numpy<2.0 is a hard ABI pin recorded in the
upstream environment.yml comments; do not mix packages into the seismic
environments or install numeric stack pieces via pip.

Coseismic capture is a project rule set, not an upstream feature: the
magnitude threshold, AOI buffer, window lengths, and especially the
per-event bracket rule (a clean pair brackets one threshold event alone;
pairs spanning two events carry both signals) are defined by the
seismic-insar skill and validated on the Eryuan sequence. The paper's
pair-quality scoring (NDVI/snow/precipitation/land cover) guides network
construction but does not decide coseismic brackets. HyP3's free quota
discipline — only user-confirmed coseismic pairs, never the full baseline
network — is mandatory.

Two explicit decision gates precede cloud costs: `insar.confirmed` after
reviewing insar_jobs.json (AOI/windows/brackets), and
`insar.pairs_confirmed` after reviewing the pair network. Earthdata
credentials (`~/.netrc`) are a prerequisite; a failed capture (no
detectable signal for an M-threshold event) is a scientific result about
depth/magnitude detectability, not a pipeline failure.

Cross-region policy: atmospheric/ionospheric correction and detectability
thresholds are REGION decisions, never inherited from a previous region.
Tropospheric correction is decided AFTER first maps from evidence (expected
signal scale vs atmospheric noise; stripe morphology; asc/desc consistency),
applied via GACOS or PyAPS/ERA5 when triggered, with both raw and corrected
maps delivered; ionospheric correction follows band/latitude rules (C-band
off, L-band/high-latitude on). The magnitude threshold, coherence threshold
and the look-direction heuristic verification are explicit per-region
checkpoints. When evidence is ambiguous, correction credentials are
missing, or the event is scientifically significant, the agent asks the
user instead of deciding silently.

- [Stage policy](../../skills/seismic-insar/SKILL.md)
- [Vendored provenance + env/ABI notes](../../knowledge/repos/InSARHub/VENDORED.md)
- [Event selection + brackets](../../skills/seismic-insar/scripts/1_select_events.py)
- [Scene search + pairs](../../skills/seismic-insar/scripts/2_run_downloader.py)
- [HyP3 submission](../../skills/seismic-insar/scripts/3_run_processor.py)
- [Product manifest](../../skills/seismic-insar/scripts/4_collect_products.py)
- [Initial settings](../../../configs/pipeline.example.json)

## Wiki reading route

- [InSARHub](../library/wiki/entities/insarhub.md)
- [InSARHub paper](../library/wiki/sources/li-2026-insarhub.md)
- [InSARHub v0.4.2 docs](../library/wiki/sources/insarhub-docs-v042.md)
