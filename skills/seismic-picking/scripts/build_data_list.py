#!/usr/bin/env python3
"""Build EQNet data_list from a preprocess archive.

Selects group-days eligible for picking (manifest status READY/PARTIAL_DAY with
usable_3c_intervals) and writes one line per group-day as
"E_file,N_file,Z_file" (comma-separated, natively supported by EQNet, F9).

Archive produced before preprocess v5 is SAC; --stage-mseed converts to
MiniSEED with explicit FLOAT32 encoding (integer encodings destroy m/s-scale
values). Marked transitional: remove once the archive is natively MiniSEED.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

from contract_io import load_contract, product_path
from archive_interface import archive_records


def find_components(day_dir: Path):
    """Return {'E': path, 'N': path, 'Z': path} for one group-day dir, or None."""
    out = {}
    for comp in ("E", "N", "Z"):
        hits = sorted(day_dir.glob(f"*.{comp}.*"))
        hits = [h for h in hits if h.suffix.lower() in (".sac", ".mseed")]
        if hits:
            out[comp] = hits[0]
    return out if len(out) == 3 else None


def stage_mseed(day_dir: Path, comps: dict, stage_root: Path):
    """Transitional SAC -> MiniSEED (FLOAT32) staging. Read-only on archive."""
    import obspy
    rel = day_dir.relative_to(day_dir.anchor)  # keep layout uniqueness
    out_dir = stage_root / rel
    out_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    for comp, src in comps.items():
        dst = out_dir / (src.stem + ".mseed")
        if dst.exists():
            out[comp] = dst
            continue
        st = obspy.read(str(src))
        if len(st) != 1:
            raise ValueError(f"{src}: expected single trace")
        st[0].write(str(dst), format="MSEED", encoding="FLOAT32")
        out[comp] = dst
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True, help="preprocess archive root")
    ap.add_argument("--out", required=True, help="data_list output path")
    ap.add_argument("--stage-mseed", default=None,
                    help="transitional: stage SAC->MiniSEED(FLOAT32) under this dir")
    args = ap.parse_args()

    contract, contract_path = load_contract(args.archive, "preprocess")
    root = (contract_path.parent / contract["archive_root"]).resolve()
    manifest = product_path(args.archive, "preprocess", "manifest_path")
    if not manifest.exists():
        sys.exit(f"missing {manifest}")

    records, skipped = archive_records(root)
    lines = []
    names = set()
    for row in records:
        comps = {c: root / row["file_" + c] for c in "ZNE"}
        if any(not p.is_file() for p in comps.values()):
            raise ValueError("Missing declared archive component")
        if args.stage_mseed and next(iter(comps.values())).suffix.lower() == ".sac":
            comps = stage_mseed(next(iter(comps.values())).parent, comps, Path(args.stage_mseed))
        if any("," in str(p) or "\n" in str(p) for p in comps.values()):
            raise ValueError("EQNet data-list paths cannot contain commas or newlines")
        name = comps["Z"].name
        if name in names:
            raise ValueError("Archive filenames must include group and date to avoid EQNet output collisions")
        names.add(name)
        lines.append(",".join(str(comps[c]) for c in ("E", "N", "Z")))
    if not lines:
        raise ValueError("No eligible group-days")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n")
    (Path(args.out).with_suffix(".skipped.json")).write_text(json.dumps(skipped, indent=2))
    print(f"data_list: {len(lines)} group-days; skipped: {len(skipped)} "
          f"-> {args.out} (+ .skipped.json)")


if __name__ == "__main__":
    main()
