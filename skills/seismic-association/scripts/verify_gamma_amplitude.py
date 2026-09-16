#!/usr/bin/env python3
"""Check adapter amplitudes against the pinned GaMMA input conversion, without association.

Usage: python -B verify_gamma_amplitude.py --gamma-repo knowledge/repos/GAMMA
Uses only synthetic CSVs in a temporary directory and the existing environment.
"""
import argparse
import hashlib
import importlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

GAMMA_COMMIT = "80394dd4a4c29450da599f507916ecf1db6203dd"


def adapt(root, amplitudes, usable=None):
    root.mkdir()
    n = len(amplitudes)
    picks = pd.DataFrame({
        "station_id": ["FJ.TEST.00.HH"] * n,
        "phase_time": pd.date_range("2026-01-01T00:00:00Z", periods=n, freq="s"),
        "phase_type": ["P" if i % 2 == 0 else "S" for i in range(n)],
        "phase_score": [0.9] * n,
        "phase_amplitude": amplitudes,
        "amplitude_units": ["m/s"] * n,
        "usable_3c": usable if usable is not None else [True] * n,
    })
    picks.to_csv(root / "picks.csv", index=False)
    (root / "sta.lst").write_text("FJ.TEST.00.HH 119.9 27.2 0\n")
    adapter = Path(__file__).with_name("build_gamma_inputs.py")
    subprocess.run([
        sys.executable, "-B", str(adapter), "--picks", str(root / "picks.csv"),
        "--archive", str(root), "--stations", str(root / "sta.lst"),
        "--out", str(root / "out"),
    ], check=True, capture_output=True, text=True)
    converted = pd.read_csv(root / "out/gamma_picks.csv", parse_dates=["timestamp"])
    stats = json.loads((root / "out/input_filter_stats.json").read_text())
    assert stats["input_rows"] == (
        stats["excluded_usable_3c"] + stats["excluded_amplitude"] + stats["output_rows"]
    ), stats
    return converted, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gamma-repo", required=True)
    args = ap.parse_args()
    repo = Path(args.gamma_repo).resolve()
    commit = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    assert commit == GAMMA_COMMIT, f"Unexpected GaMMA commit: {commit}"
    source = repo / "gamma/utils.py"
    frozen_source = subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{GAMMA_COMMIT}:gamma/utils.py"])
    assert source.read_bytes() == frozen_source, "GaMMA converter differs from pinned commit"
    sys.path.insert(0, str(repo))
    gamma_utils = importlib.import_module("gamma.utils")
    assert Path(gamma_utils.__file__).resolve() == source, gamma_utils.__file__

    stations = pd.DataFrame({
        "id": ["FJ.TEST.00.HH"], "x(km)": [0.0], "y(km)": [0.0], "z(km)": [0.0],
    })
    config = {"use_amplitude": True, "dims": ["x(km)", "y(km)", "z(km)"]}
    expected_amp = np.array([1e-5, 1e-6, 5e-8, 1e-7])
    expected_internal = np.array([-3.0, -4.0, -5.301029995663981, -5.0])
    with tempfile.TemporaryDirectory(prefix="gamma-amplitude-") as temporary:
        root = Path(temporary)
        amplitudes = list(expected_amp) + [0, -1, "", "invalid", "inf", "-inf", 1e-4]
        picks, stats = adapt(root / "mixed", amplitudes, [True] * 10 + [False])
        np.testing.assert_allclose(picks["amp"], expected_amp, rtol=1e-15, atol=0)
        assert stats["excluded_usable_3c"] == 1, stats
        assert stats["amplitude_reject_reasons"] == {
            "missing_or_non_numeric": 2, "non_finite": 2, "non_positive": 2,
        }, stats
        actual = gamma_utils.convert_picks_csv(picks.copy(), stations, config)[0][:, 1]
        np.testing.assert_allclose(actual, expected_internal, rtol=0, atol=1e-12)
        assert np.isfinite(actual).all()

        # Negative control: the former adapter's pre-log must violate this check.
        wrong = picks.copy()
        wrong["amp"] = np.log10(expected_amp * 1e6)
        with np.errstate(divide="ignore", invalid="ignore"):
            wrong_internal = gamma_utils.convert_picks_csv(wrong, stations, config)[0][:, 1]
        assert not np.allclose(wrong_internal, expected_internal)
        assert not np.isfinite(wrong_internal).all()

        empty, empty_stats = adapt(root / "all_invalid", [0, -1, "nan", "inf"])
        assert empty.empty
        assert empty_stats["excluded_amplitude"] == 4, empty_stats
        assert empty_stats["output_rows"] == 0, empty_stats

    print(json.dumps({
        "status": "PASS", "gamma_commit": commit,
        "gamma_converter": str(source),
        "gamma_converter_sha256": hashlib.sha256(frozen_source).hexdigest(),
        "checks": ["linear_mps_preserved", "pinned_gamma_internal_values",
                   "invalid_amplitudes_counted", "usable_exclusion_counted",
                   "all_invalid_header_only", "prelog_negative_control"],
    }, indent=2))


if __name__ == "__main__":
    main()
