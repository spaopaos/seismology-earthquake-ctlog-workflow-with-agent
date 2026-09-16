#!/usr/bin/env python3
"""Prepare the default/estimated DBSCAN eps options; never choose or run association."""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Proj

DEFAULT_EPS = 10.0
GAMMA_COMMIT = "80394dd4a4c29450da599f507916ecf1db6203dd"
UTILS_SHA256 = "05b059be24616e057e4b31e410ac283a5eaa51e48678a4976fe576073d53f67e"


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def positive_number(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError("value must be finite and positive")
    return number


def load_gamma_utils():
    root = next(p for p in Path(__file__).resolve().parents
                if (p / "knowledge/repos/GAMMA/gamma/utils.py").is_file())
    repo = root / "knowledge/repos/GAMMA"
    from contract_io import load_contract
    from runtime_support import verify_vendor
    commit = verify_vendor(repo, GAMMA_COMMIT)
    if commit != GAMMA_COMMIT or file_hash(repo / "gamma/utils.py") != UTILS_SHA256:
        raise ValueError("GaMMA version/converter differs from the pinned source")
    sys.path.insert(0, str(repo))
    from gamma import utils
    if Path(utils.__file__).resolve() != repo / "gamma/utils.py":
        raise ValueError("A different gamma module is already imported")
    return utils


def physical_geometry(stations):
    frame = stations.copy()
    required = ["id", "longitude", "latitude", "elevation_m"]
    if any(c not in frame for c in required) or frame[required].isna().any().any():
        raise ValueError("Station IDs and longitude/latitude/elevation_m are required")
    for column in required[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    if not np.isfinite(frame[required[1:]].to_numpy()).all():
        raise ValueError("Station coordinates must be finite")
    if (frame.longitude.abs() > 180).any() or (frame.latitude.abs() > 90).any():
        raise ValueError("Station coordinates outside longitude/latitude range")
    # NET.STA.LOC.FAMILY -> NET.STA; bare station IDs stay unchanged.
    frame["physical_id"] = frame.id.astype(str).map(lambda s: ".".join(s.split(".")[:2]))
    counts = frame.groupby("physical_id")[required[1:]].nunique()
    if (counts > 1).any().any():
        raise ValueError("Instrument groups of a physical station disagree on coordinates")
    frame = frame.drop_duplicates("physical_id").copy()
    if frame.empty:
        raise ValueError("Station table is empty")
    proj = Proj(proj="aeqd", lon_0=float(np.degrees(np.arctan2(np.sin(np.radians(frame.longitude)).mean(), np.cos(np.radians(frame.longitude)).mean()))),
                lat_0=frame.latitude.median(), units="km")
    frame["x(km)"], frame["y(km)"] = proj(frame.longitude.to_numpy(), frame.latitude.to_numpy())
    frame["z(km)"] = -frame.elevation_m / 1000
    return frame


def prepare_options(stations_path, vp=6.0):
    vp = positive_number(vp)
    utils = load_gamma_utils()
    stations = pd.read_csv(stations_path)
    physical = physical_geometry(stations)
    estimate = None
    reason = None
    if len(physical) < 3:
        reason = "estimate_eps requires at least three physical stations"
    else:
        value = float(utils.estimate_eps(physical, vp, sigma=2.0))
        if math.isfinite(value) and value > 0:
            estimate = value
        else:
            reason = "estimate_eps returned a non-finite or non-positive value"
    explanation = ("dbscan_eps 控制拾取预分组的邻域大小；较小通常更快，"
                   "但可能拆散同一事件的拾取，较大通常更慢。推荐默认 10 秒。")
    prompt = (f"{explanation}按当前台网估计约为 {estimate:.2f} 秒"
              "（经验估计，并非最优值）。使用默认值还是估计值？") if estimate is not None else (
                  f"{explanation}当前无法给出可靠估计：{reason}。是否使用默认 10 秒？")
    return {
        "parameter": "dbscan_eps", "units": "s", "default_s": DEFAULT_EPS,
        "estimate": {"status": "AVAILABLE" if estimate is not None else "UNAVAILABLE",
                     "value_s": estimate, "reason": reason,
                     "method": "gamma.utils.estimate_eps", "sigma": 2.0},
        "vp_km_s": vp, "physical_station_count": len(physical),
        "input_station_rows": len(stations),
        "physical_station_ids": physical.physical_id.tolist(),
        "stations_path": str(Path(stations_path).resolve()),
        "stations_sha256": file_hash(stations_path),
        "gamma_commit": GAMMA_COMMIT, "gamma_utils_sha256": UTILS_SHA256,
        "user_prompt": prompt,
    }


def resolve_selection(options_path, stations_path, choice, selected_via, custom=None):
    options = json.loads(Path(options_path).read_text())
    if options["parameter"] != "dbscan_eps" or options["units"] != "s":
        raise ValueError("Unexpected eps options format")
    if options["stations_sha256"] != file_hash(stations_path):
        raise ValueError("Station inputs changed: regenerate eps options and confirm the choice")
    if (options["gamma_commit"] != GAMMA_COMMIT or options["gamma_utils_sha256"] != UTILS_SHA256
            or options["default_s"] != DEFAULT_EPS):
        raise ValueError("Stale or incompatible eps options")
    if selected_via not in ("pipeline_config", "conversation"):
        raise ValueError("Record the existing configuration or user conversation as selection source")
    if choice != "custom" and custom is not None:
        raise ValueError("--dbscan-eps is only valid with choice=custom")
    if choice == "default":
        value, basis = DEFAULT_EPS, "repo_default"
    elif choice == "estimated":
        if options["estimate"]["status"] != "AVAILABLE":
            raise ValueError("The estimated option is unavailable; obtain another user choice")
        value, basis = positive_number(options["estimate"]["value_s"]), "derived"
    elif choice == "custom" and custom is not None:
        value, basis = positive_number(custom), "user"
    else:
        raise ValueError("An explicit default, estimated, or custom choice is required")
    return {"value_s": value, "choice": choice, "basis": basis, "selected_via": selected_via,
            "default_s": DEFAULT_EPS, "estimate_s": options["estimate"]["value_s"],
            "vp_km_s": positive_number(options["vp_km_s"]),
            "options_path": str(Path(options_path).resolve()),
            "options_sha256": file_hash(options_path)}


def read_effective_eps(directory):
    directory = Path(directory)
    config = json.loads((directory / "effective_config.json").read_text())
    selection = json.loads((directory / "dbscan_eps_selection.json").read_text())
    value = positive_number(config["dbscan_eps"])
    if value != positive_number(selection["value_s"]):
        raise ValueError("Effective eps disagrees with the recorded user selection")
    if positive_number(config["vel"]["p"]) != positive_number(selection["vp_km_s"]):
        raise ValueError("DBSCAN velocity disagrees with eps preparation")
    return value, selection


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stations", required=True, help="GaMMA station CSV; physical or instrument-group rows")
    ap.add_argument("--vp", type=float, default=6.0, help="DBSCAN scaling Vp, km/s (default 6.0)")
    ap.add_argument("--out", required=True, help="dbscan_eps_options.json")
    args = ap.parse_args()
    options = prepare_options(args.stations, args.vp)
    Path(args.out).write_text(json.dumps(options, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(options["user_prompt"])
    print(f"Options saved to {args.out}; no value selected, association not started.")


if __name__ == "__main__":
    main()
