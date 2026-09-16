# Wiki integration and migration from v0.1.0

The 0.3.0-dev workflow revision adds a seventh execution binding, `post_detection_relocation`, for post-MESS CC+CT HypoDD. The 32 original Wiki pages and source PDFs remain unchanged. Its new execution identity requires a new run; do not rewrite old knowledge locks or append new provenance to completed analyses. The historical v0.2.0 migration notes below describe the original six-stage release.

## What happens to the two existing packages

- **v0.1.0 workflow package:** keep it as the immutable baseline for existing runs. Its scientific environments, native tools and weights are reused. Do not modify its archives or attach new Wiki provenance to results it already generated.
- **Live LLM Wiki:** keep the existing authoring project in its current location so the desktop registration continues to work. Edit/browse there. The original PDFs and the existing backup ZIP are preserved. A backup ZIP is a point-in-time copy, not a second authoring source.
- **v0.2.0 workflow package:** use this combined release for new analyses and new agents. It carries a fixed export in `knowledge/library`, six execution bindings and an ordinary CLI. No desktop application, compatibility userspace, loopback token, provider configuration or application cache is included or required.

Existing users can unpack the small v0.2.0 **upgrade archive** next to v0.1.0 and point to the same runtime mapping. The upgrade contains all workflow sources, Wiki content, binaries and weights; it omits the three large environment archives. For a new machine, use the v0.2.0 complete offline archive and deploy its environments as in README. The embedded environment bytes are the same as v0.1.0.

```bash
# Run from the new package; adapt the explicit old mapping path.
python3 seisflow.py --runtime ../seismology-agent-0.1.0/runtime.local.json doctor
python3 seisflow.py init --workdir ../runs/new-region
```

A new run may consume valid existing upstream products with their original lineage. It must not claim that the old upstream computation consulted the newly added Wiki. Resume pre-Wiki runs with their original release.

## What knowledge is included

The original collection has 32 knowledge pages, eight source PDFs and 239 physical PDF pages. Export changes only Wiki-link syntax into portable relative Markdown links; source PDFs and page-numbered texts retain their original hashes. `library/export.json` records the source snapshot and export transformation.

The 2002 HYPOINVERSE guide and original PhaseNet paper remain historical/method references. Execution bindings point to the current PhaseNet+ code/weights and the existing 1.40 manual, with an additional page-numbered extraction. HypoDD binary/source provenance remains unresolved and is labeled accordingly. The PALM paper does not establish the project's medium-template and CC-tier policy.

AutoBA, Mindat and SPECFEM background pages remain available for global research queries, but are not part of ordinary association/location parameter routes. The Wiki's original evidence-gap page describes its eight-document corpus; release bindings provide current implementation context separately.

## Query from any local agent

Knowledge commands use Python's standard library and do not require the LLM Wiki application or an LLM provider configured in that application. The calling analysis agent interprets the returned content using its own model.

```bash
python3 seisflow.py knowledge verify
python3 seisflow.py knowledge stage --stage association
python3 seisflow.py knowledge search --stage relocation --query "阻尼 条件数"
python3 seisflow.py knowledge read --id waldhauser-2001-hypodd
python3 seisflow.py knowledge source --id waldhauser-2001-hypodd --page 9
python3 seisflow.py knowledge source --id klein-2014-hypoinverse140 --page 1
```

Returned PDF page numbers are physical pages starting at 1. Inspect the PDF for figures, formulas and tables distorted by extraction. The exported Wiki remains English; the analysis agent can explain it to the user in their preferred language.

## Record what was actually used

Every executed stage verifies and pins the current knowledge identity in `knowledge.lock.json`, records it in run_state.json, and writes `knowledge/context-<stage>.json`. This records available evidence and configured stage settings. It **does not** assert that an agent read a page or that its statements were scientifically verified.

Add `--run-dir` and `--stage` to read/source commands to log which content was returned. For a key parameter explanation, cite a routed Wiki page and the actual current configuration field:

```bash
python3 seisflow.py knowledge read --id gamma \
  --stage association --run-dir ../runs/new-region

python3 seisflow.py knowledge cite --id gamma --stage association \
  --run-dir ../runs/new-region --parameter association.dbscan_eps_choice \
  --rationale "User selected the recommended 10 s option after reviewing the current network estimate; the pinned implementation defines the parameter."
```

Use the example only after that user choice really occurred and pipeline.json records it. The citation records the configuration value/hash and the agent's explanation, not a claim of completed scientific execution. Actual effective settings and trial outputs remain the scientific execution evidence. Access and citation events are append-only in `knowledge-access.jsonl`.

If the knowledge snapshot, cited code or toolchain identity changes, do not resume the old run against that changed evidence. Use the original fixed release or start a new run. Application edits belong to the live authoring project and become available to future runs through a new exported release.

## Updating after further Wiki edits

Maintain the original Wiki, then export into a **new** snapshot directory using `scripts/export_wiki.py --source <live-project> --out <new-directory>`. This authoring/export tool uses PyYAML already present in the supplied science environment. Review the stage bindings against the pinned tools, run link/source/version tests, and publish a new package with regenerated manifests. Do not overwrite `knowledge/library` inside a release while analysis is running.

In the new release workspace, after placing the reviewed export at knowledge/library, run `python3 scripts/build_knowledge_manifest.py`, then `python3 seisflow.py knowledge verify` and the knowledge tests. `scripts/build_release.py` requires that verification to pass before packaging. This operation freezes knowledge; it is not authorization to change scientific code or declare its tests passed.

Knowledge identity/link checks do not prove the scientific correctness of all 32 pages. Fact review and independent-agent/new-region evaluation retain their own evidence status. See VALIDATION.md for the actual scope of this release.
