# Deployment and publication

## Offline distribution

Unpack the complete Linux x86-64 archive. It contains the project and `runtime_archives/` with three checksummed conda-pack archives. `scripts/deploy_runtime.py` verifies the archives, extracts them into an explicitly chosen new directory, runs each environment's relocation script, and writes a relative runtime mapping. It never installs dependencies, alters existing environments, or overwrites an existing runtime directory.

Use a Python 3.8+ interpreter to deploy. Subsequent scientific execution uses the supplied Python 3.9 and 3.11 interpreters. Runtime extraction needs about 20 GB free in addition to the compressed archives; real waveform processing needs additional input/output/scratch space. Keep the original archives to deploy at another location: an already prefix-repaired environment should be re-extracted when relocating.

The science snapshot supplies ObsPy, PhaseNet+, GaMMA and numeric helpers; the validator snapshot supplies JSON Schema validation; the MESS snapshot supplies PALM dependencies. Environment names are not an interface: paths in the runtime mapping select them.

Run `seisflow.py doctor --out deployment-check.json`. The check imports dependencies, verifies source, binary and checkpoint identities, checks native dynamic libraries and tests schema availability. It is an installation preflight, not proof of scientific accuracy. Run the provided regression and smoke checks after deployment.

Target: Linux x86-64; source host: glibc 2.31. Fortran support libraries accompany the native binaries. The host supplies its ELF loader, libc and libm. Incompatible systems fail preflight; no automatic system changes occur. CPU is the validated execution path. GPU acceleration requires a separately working compatible host driver and explicit device selection; GPU portability has not been established by this release.

## Existing environments

Use `seisflow.py configure` to map three explicitly selected interpreters. A single interpreter may serve several roles if all required imports and checks succeed. Use `--out <mapping>` for a mapping outside the package, and `seisflow.py --runtime <mapping> ...` thereafter. No absolute developer path is a fallback.

## Rebuilding and provenance

`environments/*.installed.json` records actual installed Python distributions. Conda exports and explicit package inventories are included as rebuilding inputs, not a claim that an independently rebuilt environment was tested. The MESS snapshot contains an existing Conda/pip mismatch in installer metadata (setuptools in particular); only audited obsolete installer records were handled during packing, and actual runtime files were retained. See `environments/PACKAGING_NOTES.md`. Do not use that Conda record alone to infer the actual installed setuptools version.

HYPOINVERSE source and `knowledge/repos/hyp2000-1.40/build_and_verify.sh` are provided with the official testone reference. A rebuilt binary must pass its tests and be registered as a new validated build; it may have a different hash. HypoDD/ph2dt are pinned production binaries; exact matching source/build provenance is not established, so this release supports their supplied Linux build and does not promise arbitrary-platform recompilation.

## GitHub handoff

The source archive contains maintained project code, skills, contracts, tests, source snapshots and documentation. It excludes model weights, native runtime assets and the three environment archives. Add the supplied assets as release downloads and publish their SHA256SUMS. Keep upstream license notices with redistributed components. The package has not been uploaded to an external service by the packaging process.

After testing on the destination, archive the fixed release and its validation report for citation. Fill author/repository/DOI metadata from the actual publication details; no author identity or DOI is invented here.

## Wiki-aware v0.2.0 upgrade

Existing v0.1.0 users can use the upgrade archive and reuse the same three interpreters via an explicit runtime mapping. New-machine users can use the complete offline archive, whose environment hashes match the v0.1.0 environment manifest. The live LLM Wiki project stays at its authoring location; only its fixed export is included. See WIKI_INTEGRATION.md for query, citation and update commands.
