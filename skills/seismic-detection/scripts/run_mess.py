#!/usr/bin/env python3
"""One medium template library, one segmented scan, one association, three CC exports."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from contract_io import load_contract, product_path, sha256, relative
from export_cc_catalogs import export, THRESHOLDS
from mess_contracts import load_mess_contracts
from template_inputs import snapshot, identity, prepare_cache

PALM_COMMIT = "1d87476a4078442111081840444ba99b43e020da"


def segments(time_range, days=10):
    left, right = [datetime.strptime(v, "%Y%m%d") for v in time_range.split("-")]
    if left >= right or days < 1:
        raise ValueError("Use an increasing UTC date range and positive segment length")
    result = []
    while left < right:
        end = min(left + timedelta(days=days), right)
        result.append(left.strftime("%Y%m%d") + "-" + end.strftime("%Y%m%d"))
        left = end
    return result


def config_text(source, overrides):
    text = Path(source).read_text()
    for name, value in overrides.items():
        pattern = r"(?m)^(\s*)self\." + re.escape(name) + r"\s*=.*$"
        text, count = re.subn(pattern, lambda match: match[1] + "self." + name + " = " + repr(value), text)
        if count != 1:
            raise ValueError("Pinned PALM config field is missing/ambiguous: " + name)
    return text


def write_same(path, text):
    if path.exists() and path.read_text() != text:
        raise ValueError("A recorded run file changed; use a new output directory: " + str(path))
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "relocation-dir", "association-dir", "location-dir", "stations", "out", "run-id", "time-range", "python"):
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--device", choices=["cpu", "gpu"], required=True)
    ap.add_argument("--gpu-index", type=int)
    ap.add_argument("--workers", type=int, required=True)
    ap.add_argument("--segment-days", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.workers < 1 or (args.device == "gpu" and (args.gpu_index is None or args.gpu_index < 0)):
        ap.error("Provide a positive worker budget and an explicit GPU index for GPU execution")
    scripts = Path(__file__).resolve().parent
    root = next(p for p in scripts.parents if (p / "knowledge/repos/PALM").is_dir())
    palm = root / "knowledge/repos/PALM"
    from runtime_support import verify_vendor
    commit = verify_vendor(palm, PALM_COMMIT)
    contracts = load_mess_contracts(args.archive, args.relocation_dir,
                                    association=args.association_dir, location=args.location_dir)
    medium = product_path(args.relocation_dir, "relocation", "outputs.catalogs.medium")
    dc = contracts["preprocess"][0]["data_contract"]
    detection_sr = 100.0 if dc["target_band_hz"][1] > 0.8 * 25 else 50.0
    settings = {"min_snr": 2, "min_sta": 4, "trig_thres": 0.3,
                "samp_rate": detection_sr, "phase_samp_rate": dc["sampling_rate_hz"],
                "freq_band": dc["target_band_hz"], "num_workers": args.workers}
    labels = segments(args.time_range, args.segment_days)
    output = Path(args.out).resolve()
    context = {"workflow": "single_medium_library", "run_id": args.run_id,
        "template_source_tier": "medium", "medium_catalog_sha256": sha256(medium),
        "catalog_cc_thresholds": list(THRESHOLDS), "settings": settings, "palm_commit": commit,
        "time_range": args.time_range, "segments": labels, "python": str(Path(args.python).resolve()),
        "device": args.device, "gpu_index": args.gpu_index,
        "stations_sha256": sha256(args.stations),
        "contracts": {stage: {"path": str(path), "sha256": sha256(path)} for stage, (_, path) in contracts.items()},
        "scripts": {p.name: sha256(p) for p in scripts.glob("*.py")}}
    if args.dry_run:
        print(json.dumps({**context, "template_libraries": 1, "global_associations": 1,
                          "scan_jobs": len(labels), "final_catalogs": 3, "output": str(output)}, indent=2))
        return
    if not Path(args.python).is_file():
        raise ValueError("The explicitly selected scientific interpreter is missing")
    if output.exists() and any(output.iterdir()) and not (output / "run_context.json").exists():
        raise ValueError("Nonempty/untracked output directory; choose a new run directory")
    context_text = json.dumps(context, sort_keys=True, indent=2) + "\n"
    write_same(output / "run_context.json", context_text)
    context_hash = hashlib.sha256(context_text.encode()).hexdigest()
    runtime = output / "runtime_config.json"
    write_same(runtime, json.dumps(settings, sort_keys=True, indent=2) + "\n")
    rundir = output / "rundir"
    write_same(rundir / "mess_config.py", config_text(palm / "2_run_mft/config_eg.py", settings))
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(map(str, (rundir, palm / "MFT_src", palm / "PAL_src")))
    env["PALM_MFT_CONFIG"] = "mess_config"
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    def step(name, command, expected, input_digest="", validate_after=None):
        marker = output / "steps" / (name + ".json")
        expected = [Path(p).resolve() for p in expected]
        step_context = hashlib.sha256((context_hash + input_digest).encode()).hexdigest()
        if marker.exists():
            previous = json.loads(marker.read_text())
            if previous["context_sha256"] != step_context or any(
                    not p.is_file() or previous["outputs"].get(str(p)) != sha256(p) for p in expected):
                raise ValueError("Changed or stale completed step: " + name)
            return
        print("Running " + name, flush=True)
        for p in expected:
            p.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([args.python, "-B", *map(str, command)], cwd=rundir, env=env, check=True)
        if any(not p.is_file() for p in expected):
            raise ValueError("Stage failed to produce its expected files: " + name)
        if validate_after is not None:
            validate_after()
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"context_sha256": step_context,
            "outputs": {str(p): sha256(p) for p in expected}}, indent=2) + "\n")
    adapter = output / "adapter"
    step("derive", [scripts / "derive_params.py", "--archive", Path(args.archive).resolve(),
        "--relocation-dir", Path(args.relocation_dir).resolve(), "--stations", Path(args.stations).resolve(),
        "--out", output / "derived"], [output / "derived/derived_quantities.json"])
    step("adapt", [scripts / "adapt_to_palm.py", "--archive", Path(args.archive).resolve(),
        "--relocation-dir", Path(args.relocation_dir).resolve(), "--association-dir", Path(args.association_dir).resolve(),
        "--out", adapter, "--time-range", args.time_range], [adapter / "templates.temp", adapter / "data_fingerprint.json", adapter / "template_source.json", adapter / "continuous_manifest.json"])
    from station_identity import resolve_groups
    selected = json.loads((adapter / "continuous_manifest.json").read_text())["selected_groups"]
    coordinates = resolve_groups(args.stations, selected.values()).set_index("id")
    positions = {physical: tuple(coordinates.loc[group, ["longitude", "latitude", "elevation_m"]])
                 for physical, group in selected.items()}
    codes = set()
    for line in (adapter / "templates.temp").read_text().splitlines():
        fields = line.split(",")
        if len(fields) == 3:
            codes.add(fields[0])
    station_lines = []
    for code in sorted(codes):
        lon, lat, elev = positions[code]
        station_lines.append(f"{code},{lat},{lon},{elev},1.0\n")
    station_file = rundir / "stations.sta"
    write_same(station_file, "".join(station_lines))
    source_snapshot = snapshot(adapter, runtime)
    source_digest = identity(source_snapshot)
    store = prepare_cache(output, source_snapshot)
    def unchanged_template_sources():
        if snapshot(adapter, runtime) != source_snapshot:
            raise ValueError("Template source changed during cutting; incomplete cache cannot be used")
    step("cut_" + source_digest, [palm / "MFT_src/cut_template.py", "--data_dir", adapter / "continuous",
        "--temp_pha", adapter / "templates.temp", "--out_root", store],
        [store / "template_manifest.json", store / "template_index.npy", store / "source_snapshot.json"],
        source_digest, unchanged_template_sources)
    verification = output / "mess_input_verification.json"
    # Always recheck inputs on resume, including actual template index/shards.
    subprocess.run([args.python, "-B", str(scripts / "verify_mess_inputs.py"), "--archive", str(Path(args.archive).resolve()),
        "--workdir", str(adapter), "--template-store", str(store), "--runtime-config", str(runtime),
        "--out", str(verification)], env=env, cwd=rundir, check=True)
    verification_hash = sha256(verification)
    verified_waveforms = json.loads(verification.read_text())["continuous_sha256"]
    def unchanged_scan_sources():
        if any(not Path(path).is_file() or sha256(path) != digest for path, digest in verified_waveforms.items()):
            raise ValueError("Waveforms changed during scanning; incomplete scan cannot be used")
    phase_files = []
    for label in labels:
        catalog, phase = output / "scan" / ("catalog_" + label + ".dat"), output / "scan" / ("phase_" + label + ".dat")
        code = palm / "MFT_src" / ("run_mft_gpu.py" if args.device == "gpu" else "run_mft.py")
        command = [code, "--data_dir", adapter / "continuous", "--time_range", label,
            "--sta_file", station_file, "--temp_root", store, "--temp_pha", adapter / "templates.temp",
            "--out_ctlg", catalog, "--out_pha", phase]
        if args.device == "gpu":
            command += ["--gpu_idx", str(args.gpu_index)]
        step("scan_" + label, command, [catalog, phase], verification_hash, unchanged_scan_sources)
        phase_files.append(phase)
    associated = output / "associated"
    files = {"catalog": associated / "catalog.csv", "phase": associated / "phase.csv",
             "event": associated / "event.dat", "dt_cc": associated / "dt.cc"}
    step("associate", [palm / "MFT_src/associate_mft.py", "--det_pha", *phase_files,
        "--temp_pha", adapter / "templates.temp", "--sta_file", station_file, "--time_range", args.time_range,
        "--out_catalog", files["catalog"], "--out_phase", files["phase"], "--out_event", files["event"], "--out_dt", files["dt_cc"]], list(files.values()), verification_hash)
    files["templates"] = adapter / "templates.temp"
    files.update(runtime_config=runtime, config_python=rundir / "mess_config.py", input_verification=verification,
                 template_manifest=store / "template_manifest.json", template_index=store / "template_index.npy",
                 template_source_snapshot=store / "source_snapshot.json")
    scan_manifest = {"workflow": "single_medium_library", "state": "ASSOCIATED", "run_id": args.run_id,
        "palm_commit": commit, "template_source_tier": "medium", "catalog_cc_thresholds": list(THRESHOLDS),
        "hypodd_depth_offset_km": 5.0,
        "processing": {"band_hz": settings["freq_band"], "sampling_rate_hz": detection_sr, "min_snr": 2},
        "contracts": {stage: str(path) for stage, (_, path) in contracts.items()},
        "files": {name: {"path": relative(path, output), "sha256": sha256(path)} for name, path in files.items()}}
    manifest_path = output / "scan_manifest.json"
    write_same(manifest_path, json.dumps(scan_manifest, sort_keys=True, indent=2) + "\n")
    products = output / "catalogs"
    print(json.dumps(export(manifest_path, products), indent=2))


if __name__ == "__main__":
    main()
