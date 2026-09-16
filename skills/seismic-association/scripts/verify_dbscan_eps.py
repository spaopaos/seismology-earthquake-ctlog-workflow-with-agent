#!/usr/bin/env python3
"""Exercise eps preparation, explicit choices, and contract records using synthetic files.

Runs the actual runner only with --prepare-only; never calls association.
"""
import json
import os
import subprocess
import sys
import tempfile
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from prepare_dbscan_eps import load_gamma_utils, physical_geometry, read_effective_eps
from qc_and_contract import dbscan_contract_params


def run(script, arguments, env, ok=True):
    result = subprocess.run([sys.executable, "-B", str(script), *map(str, arguments)],
                            capture_output=True, text=True, env=env)
    if ok and result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    if not ok and result.returncode == 0:
        raise AssertionError("Expected refusal, but command succeeded")
    return result


def main():
    scripts = Path(__file__).resolve().parent
    utils = load_gamma_utils()
    with tempfile.TemporaryDirectory(prefix="gamma-eps-") as temporary:
        root = Path(temporary)
        env = os.environ.copy()
        env["MPLCONFIGDIR"] = str(root / "mpl")
        stations = pd.DataFrame({
            "id": ["FJ.A.00.HH", "FJ.A.20.HN", "FJ.B.00.HH", "FJ.C.00.HH"],
            "longitude": [119.8, 119.8, 119.85, 119.9],
            "latitude": [27.2] * 4, "elevation_m": [100.0] * 4,
        })
        station_path = root / "stations.csv"
        stations.to_csv(station_path, index=False)
        options_path = root / "options.json"
        run(scripts / "prepare_dbscan_eps.py",
            ["--stations", station_path, "--out", options_path], env)
        options = json.loads(options_path.read_text())
        assert options["default_s"] == 10.0
        assert options["physical_station_count"] == 3 and options["input_station_rows"] == 4
        native = float(utils.estimate_eps(physical_geometry(stations), 6.0))
        assert 0 < native < 10.0
        np.testing.assert_allclose(options["estimate"]["value_s"], native, rtol=1e-14)
        assert "value_s" not in options, "Preparation must not select a value"

        pd.DataFrame({"id": ["FJ.A.00.HH"], "timestamp": ["2026-01-01T00:00:00Z"],
                      "type": ["p"], "prob": [0.9], "amp": [1e-5]}).to_csv(root / "picks.csv", index=False)
        raw = root / "picking_raw.csv"
        pd.DataFrame({"station_id": ["FJ.A.00.HH"], "phase_time": ["2026-01-01T00:00:00Z"],
                      "phase_type": ["P"], "phase_score": [0.9], "phase_amplitude": [1e-5], "instrument_family": ["HH"], "polarity_score": [0.8]}).to_csv(raw, index=False)
        upstream = {"contract_version": "2.0", "stage": "picking", "software": {"name": "synthetic fixture"},
            "run_id": "eps-unit-fixture", "created_at": "2026-01-01T00:00:00Z", "upstream": [], "status": "PARTIAL",
            "artifacts": {"picks": {"path": raw.name, "kind": "file", "required": True,
                                      "sha256": hashlib.sha256(raw.read_bytes()).hexdigest()}},
            "reader": {"name": "synthetic", "input_verification": {"status": "NOT_TESTED"}},
            "component_order": ["E", "N", "Z"], "normalization": "none", "model": {"weights": "synthetic"},
            "window": {"mode": "whole_day", "sampling_rate_hz": 100.0}, "thresholds": {"min_prob": 0.3},
            "interval_policy": "picks_outside_usable_3c_flagged",
            "outputs": {"picks_path": raw.name, "schema": list(pd.read_csv(raw).columns), "time_base": "UTC"},
            "coverage": {"station_days_processed": 1}, "stats": {"n_p": 1, "n_s": 0}}
        (root / "picking.json").write_text(json.dumps(upstream))
        prepared = pd.read_csv(raw)
        for alias, source in {"id": "station_id", "timestamp": "phase_time", "type": "phase_type", "prob": "phase_score", "amp": "phase_amplitude"}.items():
            prepared[alias] = prepared[source]
        prepared["type"] = prepared["type"].str.lower()
        prepared["source_pick_index"] = [0]
        prepared.to_csv(root / "picks.csv", index=False)
        (root / "input_manifest.json").write_text(json.dumps({
            "source_picks": {"path": str(raw), "sha256": hashlib.sha256(raw.read_bytes()).hexdigest()},
            "outputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [root / "picks.csv", station_path]}}))
        (root / "vp.cre").write_text("VP\n6.0 0.0\n6.5 10.0\n")
        (root / "vs.cre").write_text("VS\n3.5 0.0\n3.8 10.0\n")
        base = ["--picks", root / "picks.csv", "--stations", station_path,
                "--vp-model", root / "vp.cre", "--vs-model", root / "vs.cre",
                "--picking-contract", root / "picking.json",
                "--dbscan-eps-options", options_path,
                "--dbscan-eps-selected-via", "conversation", "--prepare-only"]

        refused = run(scripts / "run_gamma.py", base + ["--out", root / "no_choice"], env, ok=False)
        assert "--dbscan-eps-choice" in refused.stderr
        assert not (root / "no_choice").exists()

        for choice, expected in [("default", 10.0), ("estimated", native)]:
            output = root / choice
            run(scripts / "run_gamma.py", base + ["--out", output, "--dbscan-eps-choice", choice], env)
            value, selection = read_effective_eps(output)
            assert value == expected and selection["choice"] == choice
            config = json.loads((output / "effective_config.json").read_text())
            assert config["vel"]["p"] == options["vp_km_s"]
            assert config["eikonal"]["vel"]["p"] == [6.0, 6.5]
            assert not (output / "gamma_events.csv").exists()
            assert f"dbscan_eps = {expected!r} s" in (output / "config_rationale.md").read_text()

            # Exercise the real contract builder's parameter function. Full QC/schema
            # validation is a separate check and requires its jsonschema dependency.
            params = dbscan_contract_params(output, output / "config_rationale.md")
            assert params["dbscan_eps_s"] == expected
            assert params["dbscan_eps_estimate_s"] == native
            assert params["dbscan_eps_choice"] == choice

        custom_base = base.copy()
        custom_base[custom_base.index("conversation")] = "pipeline_config"
        run(scripts / "run_gamma.py", custom_base + ["--out", root / "custom",
            "--dbscan-eps-choice", "custom", "--dbscan-eps", "20"], env)
        value, selection = read_effective_eps(root / "custom")
        assert value == 20.0 and selection["selected_via"] == "pipeline_config"
        run(scripts / "run_gamma.py", base + ["--out", root / "invalid_custom",
            "--dbscan-eps-choice", "custom", "--dbscan-eps", "nan"], env, ok=False)

        # Changing the input invalidates the previously offered estimate.
        station_path.write_text(station_path.read_text() + "\n")
        refused = run(scripts / "run_gamma.py", base + ["--out", root / "stale",
            "--dbscan-eps-choice", "estimated"], env, ok=False)
        assert "Station inputs changed" in refused.stderr
        assert not (root / "stale").exists()

        stations.iloc[[0, 2]].to_csv(station_path, index=False)
        prepared_manifest = json.loads((root / "input_manifest.json").read_text())
        prepared_manifest["outputs"][station_path.name] = hashlib.sha256(station_path.read_bytes()).hexdigest()
        (root / "input_manifest.json").write_text(json.dumps(prepared_manifest))
        run(scripts / "prepare_dbscan_eps.py", ["--stations", station_path, "--out", options_path], env)
        unavailable = json.loads(options_path.read_text())
        assert unavailable["estimate"]["status"] == "UNAVAILABLE"
        assert unavailable["estimate"]["value_s"] is None
        refused = run(scripts / "run_gamma.py", base + ["--out", root / "unavailable",
            "--dbscan-eps-choice", "estimated"], env, ok=False)
        assert "estimated option is unavailable" in refused.stderr
        run(scripts / "run_gamma.py", base + ["--out", root / "fallback",
            "--dbscan-eps-choice", "default"], env)
        assert read_effective_eps(root / "fallback")[0] == 10.0

        # A report must not silently accept a value differing from the actual configuration.
        config_path = root / "default/effective_config.json"
        config = json.loads(config_path.read_text())
        config["dbscan_eps"] = 75.0
        config_path.write_text(json.dumps(config))
        try:
            read_effective_eps(root / "default")
        except ValueError:
            pass
        else:
            raise AssertionError("Mismatched selection/effective eps was accepted")

    print(json.dumps({"status": "PASS", "checks": [
        "native_estimator_with_physical_stations", "no_automatic_choice",
        "default_and_estimated_exact_values", "config_rationale_contract_parameter_agreement",
        "explicit_existing_configuration", "invalid_custom_rejected",
        "stale_input_rejected", "unavailable_estimate_requires_another_choice",
        "effective_selection_mismatch_rejected",
    ]}, indent=2))


if __name__ == "__main__":
    main()
