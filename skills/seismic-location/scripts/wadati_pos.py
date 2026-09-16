#!/usr/bin/env python3
"""Wadati analysis: derive Vp/Vs (pos) and intercept b from associated P/S picks.

Manual-prescribed method (HYPOINVERSE v1.40, p.10): "Make a plot of Stt versus
Ptt for your data to determine pos and b." We use S-P vs P times (Wadati) --
same data, slope = pos - 1.

Input: association gamma_picks.csv (event_index >= 0).
Output: wadati.png + wadati_result.json (pos, b, n_pairs, residual stats).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from contract_io import product_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assoc-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    picks = pd.read_csv(product_path(args.assoc_dir, "association", "outputs.assignments_path"), parse_dates=["phase_time"])
    picks = picks[picks["event_index"] >= 0]
    events = pd.read_csv(product_path(args.assoc_dir, "association", "outputs.events_path"), parse_dates=["time"])
    picks["phase_time"] = pd.to_datetime(picks["phase_time"], utc=True)
    events["time"] = pd.to_datetime(events["time"], utc=True)
    ot_map = dict(zip(events["event_id"].str.replace("gm", "").astype(int), events["time"]))

    # P/S pairs per (event, station group)
    p = picks[picks["phase_type"] == "P"].set_index(["event_index", "station_id"])
    s = picks[picks["phase_type"] == "S"].set_index(["event_index", "station_id"])
    both = p.join(s, lsuffix="_p", rsuffix="_s", how="inner")

    ot = pd.Series([ot_map[i] for i in both.index.get_level_values(0)],
                   index=both.index, dtype="datetime64[ns, UTC]")
    tp = both["phase_time_p"]
    ts = both["phase_time_s"]
    ptt = (tp - ot).dt.total_seconds()   # absolute P travel time
    stt = (ts - ot).dt.total_seconds()   # absolute S travel time
    sp = stt - ptt

    valid = (ptt > 0) & (stt > ptt) & (ptt < 300)
    ptt, stt, sp = ptt[valid], stt[valid], sp[valid]
    if len(ptt) < 3 or ptt.nunique() < 2:
        result = {"status": "INSUFFICIENT_DATA", "n_valid": len(ptt), "pos_least_squares": None,
                  "pos_wadati_median": None, "reason": "At least three valid pairs and distinct P travel times are required"}
        (out / "wadati_result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        return

    # classic Wadati: (S-P) vs P travel time, slope = pos - 1 (through origin)
    pos_wadati = float((sp / ptt).median() + 1.0)
    # manual p.10: Stt vs Ptt -> slope = pos, intercept = b
    x, y = ptt.to_numpy(), stt.to_numpy()
    A = np.vstack([x, np.ones_like(x)]).T
    pos_ls, b_ls = np.linalg.lstsq(A, y, rcond=None)[0]
    resid = y - (pos_ls * x + b_ls)

    import matplotlib
    matplotlib.use("agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(x, y, s=1, alpha=0.3)
    xx = np.linspace(0, x.max(), 10)
    ax.plot(xx, pos_ls * xx + b_ls, "r-",
            label=f"Stt vs Ptt fit: pos={pos_ls:.3f}, b={b_ls:.2f}s")
    ax.plot(xx, pos_wadati * xx, "g--", label=f"Wadati median: pos={pos_wadati:.3f}")
    ax.set_xlabel("P travel time (s)")
    ax.set_ylabel("S travel time (s)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "wadati.png", dpi=160)

    result = {"n_pairs": int(len(both)), "n_valid": int(valid.sum()),
              "pos_least_squares": round(float(pos_ls), 4),
              "b_s": round(float(b_ls), 3),
              "pos_wadati_median": round(pos_wadati, 4),
              "residual_std_s": round(float(resid.std()), 3),
              "method": "Stt vs Ptt fit + classic Wadati (manual v1.40 p.10)"}
    (out / "wadati_result.json").write_text(json.dumps(result, indent=2))
    print(result)


if __name__ == "__main__":
    main()
