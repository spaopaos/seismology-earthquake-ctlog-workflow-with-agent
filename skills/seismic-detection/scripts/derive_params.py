#!/usr/bin/env python3
"""MESS derive_params: compute derived quantities from upstream contracts (R8).

Deterministic computation only -- no LLM. Reads the preprocess archive contract
and relocation contract, applies PALM conventions, writes derived_quantities.json
with formula + inputs + result for every quantity.
"""
import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from contract_io import load_contract, product_path
from mess_contracts import load_mess_contracts

PALM_DETECTION_SR = 50.0  # PALM convention: detection at 50 Hz (Nyquist 25)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True, help="preprocess archive root")
    ap.add_argument("--relocation-dir", required=True)
    ap.add_argument("--stations", required=True, help="sta lon lat elev")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    chain = load_mess_contracts(args.archive, args.relocation_dir)
    contract, _ = chain["preprocess"]
    dc = contract["data_contract"]  # 真实契约嵌套在 data_contract 下
    band = dc["target_band_hz"]
    sr = float(dc["sampling_rate_hz"])

    # 1) Nyquist conflict vs PALM detection sampling
    palm_nyq = PALM_DETECTION_SR / 2
    nyquist_conflict = band[1] > 0.8 * palm_nyq
    detection_sr = PALM_DETECTION_SR if not nyquist_conflict else sr
    paths = {"A_native_sr": "检测跑归档原生采样率（指纹零分裂）",
             "B_derived_copy": "抗混叠低通 <=0.8*Nyquist + 降采样（derived_copy_path 记录）"}

    # 2) network aperture from station list
    sta = pd.read_csv(args.stations, sep=r"\s+", header=None,
                      names=["id", "longitude", "latitude", "elevation_m"])
    coords = sta[["longitude", "latitude"]].to_numpy()
    lat0 = coords[:, 1].mean()
    dmax = max((np.hypot((a[0]-b[0])*np.cos(np.radians(lat0))*111.32,
                         (a[1]-b[1])*111.32) for a, b in combinations(coords, 2)),
               default=0.0)

    # The sole template source is the medium HypoDD catalog.
    medium = product_path(args.relocation_dir, "relocation", "outputs.catalogs.medium")
    template_count = len(pd.read_csv(medium))

    derived = {
        "inputs": {"archive_band_hz": band, "archive_sampling_rate_hz": sr,
                   "palm_detection_sr": PALM_DETECTION_SR},
        "nyquist": {"formula": "band_high > 0.8 * (palm_detection_sr/2)",
                    "palm_nyquist_hz": palm_nyq, "conflict": nyquist_conflict,
                    "detection_sr_chosen": detection_sr,
                    "legal_paths": paths},
        "network": {"aperture_km": round(float(dmax), 2),
                    "formula": "max pairwise station distance (aeqd approx)"},
        "template_source": {"tier": "medium", "catalog_path": str(medium),
                            "candidate_events": template_count},
        "catalog_cc_thresholds": [0.4, 0.6, 0.8],
        "scan_trigger_cc": 0.3,
        "min_snr": 2,
        "min_sta_floor": 4,
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "derived_quantities.json").write_text(
        json.dumps(derived, indent=2, ensure_ascii=False))
    print(json.dumps({"nyquist_conflict": nyquist_conflict,
                      "detection_sr": detection_sr,
                      "aperture_km": derived["network"]["aperture_km"]}))


if __name__ == "__main__":
    main()
