# Seismology Agent — workflow revision 0.3.0-dev

Agent-guided seismology workflow: PhaseNet+ picking, GaMMA association, HYPOINVERSE location, HypoDD relocation and PALM MESS detection — from raw waveforms to multi-grade earthquake catalogs（全CUG（武汉）最好用的指导agent从连续波形到地震目录制作框架）.

## Three steps to a catalog

1. **Get the package** — clone this repository, download the assets of the [v0.3.0-dev release](../../releases/tag/v0.3.0-dev), and run `scripts/restore_offline_assets.sh <download-dir>` to restore the runtime archives, model weights and native binaries.
2. **Hand it to an agent** — point the agent at [AGENTS.md](AGENTS.md). It is self-contained; the agent reads the docs and skills it needs. No conversation history is required.
3. **Point it at your data** — give the agent your raw waveforms, response information and station metadata, plus a new run directory. The agent writes the dataset-specific preprocessing and then drives the stages `preprocess → picking → association → location → relocation → detection → post_detection_relocation`, pausing at documented decision points (GaMMA eps, HypoDD DAMP) for your confirmation.

Deployment commands and runtime options: [Environment setup and deployment](#environment-setup-and-deployment) below, and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

A reusable workflow for a general agent to prepare regional seismic data and execute PhaseNet+, GaMMA, HYPOINVERSE, first-round CT HypoDD, PALM MESS, and post-MESS joint CC+CT HypoDD. The final joint stage uses independent PhaseNet+ arrivals for CT and produces exactly three CC-threshold catalogs. The agent adapts uncertain raw input layouts; standardized archives, maintained converters, versioned tools, contracts and QC connect the scientific stages.

The 0.3.0-dev revision adds `post_detection_relocation` after `detection`. Read [post-MESS joint relocation](docs/POST_MESS_RELOCATION.md) for inputs, parameters, output states and migration. Start a new run when adopting this revision; retain old run contracts and knowledge locks.

**Start with [AGENTS.md](AGENTS.md) when handing this package to another agent.** No conversation history is required. Project-authored code uses MIT; third-party software retains its own terms.

This release targets **Linux x86-64** and includes pinned native binaries and a local PhaseNet+ checkpoint in the offline distribution. Its environment snapshots originate from a glibc 2.31 host. Run the compatibility checks on the destination machine. See [validation scope](docs/VALIDATION.md); another physical machine and another observed region must be evaluated there before claiming they have been tested.

## Existing v0.1.0 users

Unpack the v0.2.0 upgrade archive beside the old package. Reuse the old explicit runtime mapping (`--runtime /path/to/v0.1.0/runtime.local.json`) or configure the same three interpreters. No environment reinstall or repacking is needed. Start new analyses with v0.2.0; use v0.1.0 to inspect/resume its existing runs without assigning new knowledge provenance retroactively.

The maintained Wiki remains in its original authoring folder. This package contains 32 exported pages, their eight original PDFs/texts, six execution bindings and access to the supplied HYPOINVERSE 1.40 manual. See [Wiki integration](docs/WIKI_INTEGRATION.md).

## Environment setup and deployment

For the offline distribution, deploy the supplied existing-environment snapshots to a new directory:

```bash
python3 scripts/deploy_runtime.py --archives runtime_archives \
  --destination ./runtime --mapping ./runtime.local.json
./runtime/phasenet_plus/bin/python seisflow.py doctor --out deployment-check.json
./runtime/phasenet_plus/bin/python seisflow.py init --workdir /path/to/new-region-run
```

For an existing suitable installation, explicitly map its interpreters instead:

```bash
python3 seisflow.py configure \
  --science-python /path/to/science/bin/python \
  --validator-python /path/to/schema/bin/python \
  --mess-python /path/to/mess/bin/python
python3 seisflow.py doctor
```

Give the agent the package location, run directory, raw inputs, responses and station metadata. Read [archive interface](docs/ARCHIVE_INTERFACE.md) and [supported regional inputs](docs/SUPPORTED_INPUTS.md). The agent writes the dataset-specific preprocessing code and fills `pipeline.json`; then:

```bash
./runtime/phasenet_plus/bin/python seisflow.py run \
  --config /path/to/new-region-run/pipeline.json --stage preprocess
./runtime/phasenet_plus/bin/python seisflow.py run \
  --config /path/to/new-region-run/pipeline.json --stage picking
```

Continue with `association`, `location`, `relocation`, `detection`, `post_detection_relocation`, or use `all` to consume validated earlier stages. GaMMA pauses before association when the eps choice is missing. HypoDD needs a justified current Vp/Vs; both rounds require current DAMP evidence. Inspect QC and log files before accepting scientific interpretations.

## What is delivered

- Seven maintained skills and their deterministic stage tools.
- A portable Wiki snapshot, stage-aware search/read/source commands and per-run knowledge provenance.
- Runtime mapping, regional input normalization and resumable stage entry.
- Independent standardized-archive validation and normalized picking CSV.
- Reversible native station aliases, explicit model units/datum and layered model checks.
- Pinned upstream source snapshots with file hashes, binaries, model weights and environment inventories.
- Contract schemas, regression tests, labeled synthetic examples, deployment and new-agent guidance.

The Git source archive excludes large binary/weight/environment assets, which are supplied separately in release assets. The complete offline archive contains both. Scientific user inputs and private case outputs are not part of the package. See [distribution instructions](docs/DEPLOYMENT.md) and [third-party provenance](THIRD_PARTY.md).

## Scope

The target is a checkable scientific product. MESS detection locations inherit templates; the subsequent joint HypoDD stage supplies separately labeled relocated coordinates where supported. Missing CC/CT or DAMP evidence is reported explicitly. Event identity and physical location accuracy still require scientific review. Absolute magnitude calibration, focal mechanisms, InSAR and arbitrary 3-D models are outside this revision.

Run-state portability currently supports starting a new region on a new machine. Interrupted MESS caches retain physical paths and must be rebuilt at a new location. Standard outputs and contracts should be kept with their complete upstream data/evidence; do not copy a single catalog and expect its lineage to remain valid.
