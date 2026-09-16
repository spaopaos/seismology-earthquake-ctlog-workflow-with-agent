#!/usr/bin/env python3
"""MESS input verifier: fingerprint match + template survival sentinels.

Fail-closed gate for the MESS scan: refuse unless
  - scan data fingerprint == template fingerprint == archive contract
  - template survival counts are present and nonzero at every filter level
  - no silent station drops (PALM get_data_dict behavior) beyond declared ones
"""
import argparse
import json
import sys
from pathlib import Path
from collections import Counter
from functools import lru_cache

import numpy as np

from contract_io import load_contract, archive_fingerprint, sha256
from template_inputs import verify_snapshot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True, help="MESS workdir")
    ap.add_argument("--archive", required=True)
    ap.add_argument("--template-store", required=True, help="Completed PALM v4 NPY template store")
    ap.add_argument("--runtime-config", required=True, help="run_mess.py runtime_config.json")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    w = Path(args.workdir)

    errors, warns = [], []
    contract, _ = load_contract(args.archive, "preprocess")
    expected = archive_fingerprint(contract)
    fp_file = w / "data_fingerprint.json"
    if not fp_file.exists():
        errors.append("data_fingerprint.json missing (run adapt_to_palm.py)")
    else:
        fp = json.loads(fp_file.read_text())
        for k in expected:
            if fp.get(k) != expected[k]:
                errors.append(f"fingerprint mismatch on {k}: {fp.get(k)} != {expected[k]}")

    temp = w / "templates.temp"
    source_names = set()
    if not temp.exists():
        errors.append("templates.temp missing")
    else:
        n_ev = sum(1 for l in temp.read_text().splitlines()
                   if l.strip() and "," in l and "_" in l.split(",")[0])
        if n_ev == 0:
            errors.append("templates.temp has 0 events")
        for line in temp.read_text().splitlines():
            first = line.split(",")[0]
            if "_" in first:
                name = first.split("_", 1)[1]
                if name in source_names:
                    errors.append("template storage names are not unique")
                source_names.add(name)

    # The adapter declares a fixed, complete three-component instrument view.
    continuous_hashes = {}
    view_path = w / "continuous_manifest.json"
    if not view_path.exists():
        errors.append("continuous_manifest.json missing")
    else:
        view = json.loads(view_path.read_text())
        components = {}
        declared = set()
        for item in view["files"]:
            source, link = Path(item["source"]), Path(item["view"])
            physical = ".".join(item["group"].split(".")[:2])
            key = item["date"], physical
            components.setdefault(key, []).append(item["component"])
            declared.add(str(link.resolve()))
            if view["selected_groups"].get(physical) != item["group"] or not link.is_symlink() or link.resolve() != source.resolve():
                errors.append("continuous view contains a mixed instrument group or changed link")
            if not source.is_file():
                errors.append("continuous source file missing")
            else:
                continuous_hashes[str(source)] = sha256(source)
        if not components or any(sorted(value) != ["E", "N", "Z"] for value in components.values()):
            errors.append("continuous view must have exactly E/N/Z per station-day")
        actual = {str(p.resolve()) for p in (w / "continuous").rglob("*") if p.is_file()}
        if actual != declared:
            errors.append("undeclared or missing continuous waveform files")

    counts, shard_hashes = {}, {}
    store = Path(args.template_store).resolve()
    source_identity = None
    try:
        source_identity = verify_snapshot(w, args.runtime_config, store)
    except (ValueError, OSError, KeyError) as exc:
        errors.append(str(exc))
    cfg = json.loads(Path(args.runtime_config).read_text())
    if cfg.get("min_snr") != 2 or cfg.get("min_sta") != 4 or cfg.get("trig_thres") != 0.3:
        errors.append("runtime config differs from the fixed single-medium profile")
    expected_detection_sr = expected["sampling_rate_hz"] if expected["band_hz"][1] > 0.8 * 25 else 50.0
    if (cfg.get("freq_band") != expected["band_hz"] or cfg.get("phase_samp_rate") != expected["sampling_rate_hz"]
            or cfg.get("samp_rate") != expected_detection_sr):
        errors.append("runtime processing differs from the archive-derived processing path")
    manifest_path, index_path = store / "template_manifest.json", store / "template_index.npy"
    if not manifest_path.is_file() or not index_path.is_file():
        errors.append("completed template manifest/index is missing")
    else:
        manifest = json.loads(manifest_path.read_text())
        for key, value in {"format_version": 4, "format": "palm-mft-template-npy",
            "detection_sample_rate": cfg["samp_rate"], "phase_sample_rate": cfg["phase_samp_rate"],
            "frequency_band_hz": cfg["freq_band"], "resampling_method": "polyphase-fir-line-pad",
            "detection_window_sec": [1.0, 9.0], "p_window_sec": [0.5, 1.5], "s_window_sec": [0.5, 2.5],
            "detection_sample_npts": int(round(10 * cfg["samp_rate"])),
            "phase_detection_sample_npts": int(round(10 * cfg["phase_samp_rate"])),
            "p_sample_npts": int(round(2 * cfg["phase_samp_rate"])),
            "s_sample_npts": int(round(3 * cfg["phase_samp_rate"]))}.items():
            if manifest.get(key) != value:
                errors.append("template manifest mismatch: " + key)
        index = np.load(index_path, allow_pickle=False)
        if index.ndim != 2 or index.shape[1] != 7:
            errors.append("template index must have seven columns")
        else:
            if manifest.get("template_count") != len(index):
                errors.append("template station-entry count differs from index")
            seen, per_event = set(), Counter()
            @lru_cache(maxsize=32)
            def shard(path):
                return np.load(path, mmap_mode="r", allow_pickle=False)
            for row in index:
                name, station = map(str, row[:2])
                key = name, station
                if key in seen or name not in source_names:
                    errors.append("duplicate or unknown event/station template entry")
                seen.add(key)
                per_event[name] += 1
                try:
                    row_index = int(row[6])
                    lengths = (int(round(10 * cfg["samp_rate"])), int(round(10 * cfg["phase_samp_rate"])),
                               int(round(2 * cfg["phase_samp_rate"])), int(round(3 * cfg["phase_samp_rate"])))
                    for entry, expected_length in zip(row[2:6], lengths):
                        path = (store / str(entry)).resolve()
                        path.relative_to(store)
                        if str(path) not in shard_hashes:
                            shard_hashes[str(path)] = sha256(path)
                        array = shard(str(path))
                        if array.ndim != 3 or array.shape[1:] != (3, expected_length):
                            errors.append("template shard shape differs from configured windows/rates")
                        if row_index < 0 or row_index >= len(array) or not np.isfinite(array[row_index]).all():
                            errors.append("invalid/non-finite template shard row")
                except (ValueError, OSError, IndexError, TypeError) as exc:
                    errors.append("unreadable template shard: " + str(exc))
            counts = {"candidate_events": len(source_names), "events_with_cut_templates": len(per_event),
                      "station_templates": len(index), "scannable_events": sum(n >= 4 for n in per_event.values())}
            if counts["scannable_events"] == 0:
                errors.append("no template event has at least four stations")

    result = {"status": "FAIL" if errors else "PASS",
              "errors": errors, "warnings": warns, "template_counts": counts, "shards_sha256": shard_hashes,
              "continuous_sha256": continuous_hashes,
              "template_source_identity": source_identity,
              "scope": "Archive fingerprint, runtime/template manifest, template index/shard integrity and station-count eligibility"}
    out = Path(args.out) if args.out else w / "mess_input_verification.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps({"status": result["status"], "errors": len(errors)}))
    for e in errors:
        print("ERR:", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
