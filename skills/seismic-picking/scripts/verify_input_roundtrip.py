#!/usr/bin/env python3
"""Known-array round-trip verification of the picking read path.

Builds synthetic day files with known amplitudes, known component patterns and a
known first-motion direction on Z, then runs them through the SAME read path the
model uses (the checked shim from eqnet_pick.py). Asserts:
  - no rescaling (amplitudes preserved to float32 precision)
  - no integration (a spike stays a spike -- catches the HN trap, F1)
  - no axis swap (E/N/Z land in data indices 0/1/2, F6/F12)
  - no time shift (spike sample index preserved, F8)

Both an HH-family and an HN-family group are tested. Only when every assertion
passes may the picking contract carry input_verification: PASS.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import obspy
from obspy import UTCDateTime

SR = 100.0
NT = 60000  # 10 min is enough; full-day not needed for verification
SPIKE_IDX = 30000
AMP = {"E": 2e-6, "N": 3e-6, "Z": 1e-4}


def make_day(path: Path, net: str, sta: str, loc: str, fam: str):
    """One file per component, spike on Z at SPIKE_IDX, distinct sine levels on E/N."""
    t = np.arange(NT) / SR
    signals = {
        "E": AMP["E"] * np.sin(2 * np.pi * t),
        "N": AMP["N"] * np.cos(2 * np.pi * t),
        "Z": np.zeros(NT),
    }
    signals["Z"][SPIKE_IDX] = AMP["Z"]  # known up first motion
    files = {}
    for comp, data in signals.items():
        tr = obspy.Trace(data=data.astype(np.float32))  # FLOAT32 encoding requires float32 dtype
        tr.stats.network = net
        tr.stats.station = sta
        tr.stats.location = loc
        tr.stats.channel = fam + comp
        tr.stats.sampling_rate = SR
        tr.stats.starttime = UTCDateTime("2026-01-01T00:00:00.000")
        f = path / f"{net}.{sta}.{loc}.{fam}{comp}.20260101.vel.mseed"
        tr.write(str(f), format="MSEED", encoding="FLOAT32")  # FLOAT32 mandatory (m/s magnitudes)
        files[comp] = str(f)
    return files


def check_group(eqnet_repo: str, files: dict, fam: str):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from eqnet_pick import read_mseed_checked

    fname = ",".join(files[c] for c in ("E", "N", "Z"))
    meta = read_mseed_checked(None, fname, sampling_rate=SR)
    data = meta["waveform"].numpy()  # [3, nt, nsta] with E,N,Z order
    assert data.shape[2] == 1, f"{fam}: expected 1 station, got {data.shape[2]}"

    e, n, z = data[0, :, 0], data[1, :, 0], data[2, :, 0]
    t = np.arange(NT) / SR
    np.testing.assert_allclose(np.abs(e).max(), AMP["E"], rtol=1e-5,
                               err_msg=f"{fam}: E rescaled or swapped")
    np.testing.assert_allclose(np.abs(n).max(), AMP["N"], rtol=1e-5,
                               err_msg=f"{fam}: N rescaled or swapped")
    spike_at = int(np.argmax(np.abs(z)))
    assert spike_at == SPIKE_IDX, f"{fam}: spike moved {spike_at} != {SPIKE_IDX} (time shift)"
    assert z[SPIKE_IDX] > 0, f"{fam}: polarity flipped"
    # integration would turn the spike into a step: neighbors would stay large
    assert abs(z[SPIKE_IDX + 10]) < AMP["Z"] * 1e-3, \
        f"{fam}: spike smeared (integration? HN trap fired?)"
    assert abs(z[SPIKE_IDX] - AMP["Z"]) < AMP["Z"] * 1e-3, \
        f"{fam}: amplitude changed beyond demean tolerance"  # demean shifts spike by AMP/NT
    assert meta["dt_s"] == 1.0 / SR
    return {"family": fam, "station_id": meta["station_id"], "begin_time": meta["begin_time"],
            "spike_idx": spike_at, "status": "PASS"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eqnet-repo", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for fam, loc in (("HH", "00"), ("HN", "20")):  # HN is the trap path (F1)
        gdir = out / fam
        gdir.mkdir(exist_ok=True)
        files = make_day(gdir, "XX", "TEST", loc, fam)
        results.append(check_group(args.eqnet_repo, files, fam))
        print(f"[verify] {fam} group: PASS")

    report = out / "verify_report.json"
    report.write_text(json.dumps({"status": "PASS", "groups": results}, indent=2))
    print(f"[verify] all PASS -> {report}")


if __name__ == "__main__":
    main()
