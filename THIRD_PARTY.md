# Third-party components

Project-authored files use the root MIT license. This does not relicense upstream components.

| Component | Identity/source | Distribution role |
|---|---|---|
| EQNet / PhaseNet+ | AI4EPS/EQNet; exact commit in toolchain.json | Hashed upstream source snapshot |
| GaMMA | AI4EPS/GAMMA; exact commit in toolchain.json | Hashed upstream source snapshot |
| PALM MESS | YijianZhou/PALM integrated implementation; exact commit in toolchain.json | Hashed source, not the standalone paper MESS release |
| PhaseNet+ weights | AI4EPS/models PhaseNet-Plus-v1/model_99.pth | Official-release-identical checkpoint with SHA256 |
| HYPOINVERSE 1.40 | USGS source package, manual and testone | Source, tested build and build script |
| HypoDD / ph2dt | Pinned production Linux x86-64 binaries | Exact hashes preserved; matching source/build provenance unresolved |
| Conda/Python/CUDA packages | Per-environment metadata, license records and inventories | Existing runtime snapshots with their original notices |
| GNU Fortran support libraries | libgfortran, libquadmath, libgcc_s | Runtime dependencies; GCC notices in environments/licenses |

Upstream source license files are retained in their source directories. Model/source/binary access and redistribution terms must be represented accurately when publishing release assets; a project MIT header does not grant additional upstream rights. The offline Wiki snapshot includes eight user-supplied source PDFs and their extracted texts. They retain their publishers' terms and bibliographic attribution; the root MIT license does not relicense them. Public distribution must follow the source documents' applicable sharing terms. The local snapshot contains no desktop app state, provider credentials or compatibility runtime.
