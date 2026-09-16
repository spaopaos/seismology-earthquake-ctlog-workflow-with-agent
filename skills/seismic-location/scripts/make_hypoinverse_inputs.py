#!/usr/bin/env python3
"""GaMMA outputs -> HYPOINVERSE inputs (R1: the ONLY permitted converter).

Verified against real upstream products (2026-09-11) and golden samples
(knowledge/repos/hyp2000-1.40/testone, rushan.sta):
  - ONE phase line per event x station-group carrying P and S together
    (palm-proven layout; separate S lines misalign columns)
  - P first-motion polarity after "IP" (testone.arc golden: "IPU0")
  - real Z channel per instrument family (HHZ/HNZ/SHZ)
  - station lines follow rushan.sta: deg + space + decimal-minutes + letter,
    one line per station x instrument-group Z channel
  - HYPOINVERSE event id = integer of gm%06d (trivially reversible lineage)
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from contract_io import product_path
from station_identity import native_mapping, save_mapping

POL_MIN_SCORE = 0.3  # |polarity_score| below this -> blank polarity


def prob_to_wcode(p):
    if p >= 0.5:
        return 0
    if p >= 0.4:
        return 1
    if p >= 0.3:
        return 2
    return None


def deg_min_header(x, pos_letter, neg_letter, deg_width):
    """event header convention: deg+letter+hundredths-of-minutes (palm-proven)."""
    letter = pos_letter if x >= 0 else neg_letter
    x = abs(x)
    d = int(x)
    m = int(round(100 * 60 * (x - d)))
    if m >= 6000:
        d += 1
        m -= 6000
    return f"{d:0{deg_width}d}{letter}{m:04d}"


def deg_min_station(x, pos_letter, neg_letter):
    """station file convention (rushan.sta): deg, space, decimal minutes F7.4, letter."""
    letter = pos_letter if x >= 0 else neg_letter
    x = abs(x)
    d = int(x)
    m = 60.0 * (x - d)
    if m >= 60.0:
        d += 1
        m -= 60.0
    return f"{d:3d} {m:7.4f}{letter}"


def split_dt(dt):
    date = f"{dt.year:04d}{dt.month:02d}{dt.day:02d}"
    time = f"{dt.hour:02d}{dt.minute:02d}{dt.second:02d}{int(dt.microsecond / 1e4):02d}"
    return date, time


def z_channel(family):
    chan = str(family) + "Z"
    assert len(chan) == 3 and chan[-1] == "Z", f"bad family {family}"
    return chan


def cre2crh(src, dst, name):
    rows = [l.split() for l in Path(src).read_text().splitlines()
            if l.strip() and l.strip()[0].isdigit()]
    arr = np.array(rows, dtype=float)
    assert len(arr) > 0 and arr.shape[1] == 2 and np.isfinite(arr).all(), "invalid layered model"
    assert np.all(np.diff(arr[:, 1]) > 0), "layer tops must increase"
    assert arr[0, 1] == 0.0, "first layer top must be 0.0"
    assert np.all(np.diff(arr[:, 0]) > 0), "velocity must increase with depth"
    rounded = np.round(arr, 2)
    if any(len(f"{value:5.2f}") != 5 for value in arr.ravel()):
        raise ValueError("Model value exceeds the native CRH 5.2 field width")
    if not np.all(np.diff(rounded[:, 0]) > 0) or not np.all(np.diff(rounded[:, 1]) > 0):
        raise ValueError("Model layers become non-increasing at native CRH 0.01 precision")
    with open(dst, "w") as f:
        f.write(f"{name:<30}\n")
        for v, z in arr:
            f.write(f"{v:5.2f}{z:5.2f}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assoc-dir", required=True)
    ap.add_argument("--stations", required=True, help="sta lon lat elev (whitespace)")
    ap.add_argument("--vp-model", required=True)
    ap.add_argument("--vs-model", default=None)
    ap.add_argument("--pos", type=float, default=1.75)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    (out / "input").mkdir(parents=True, exist_ok=True)

    events = pd.read_csv(product_path(args.assoc_dir, "association", "outputs.events_path"), parse_dates=["time"])
    picks = pd.read_csv(product_path(args.assoc_dir, "association", "outputs.assignments_path"), parse_dates=["phase_time"])
    picks = picks[picks["event_index"] >= 0].copy()

    group_alias, aliases = native_mapping(args.stations, picks.station_id.unique())
    save_mapping(out / "input/station_aliases.json", aliases)

    n_lines, n_no_sta, n_dropped_w = 0, 0, 0
    used_sta_chan = set()

    with open(out / "input" / "phase.dat", "w") as fout:
        for _, e in events.iterrows():
            eid = int(str(e["event_id"]).replace("gm", ""))
            date, tme = split_dt(e["time"])
            lat = deg_min_header(e["latitude"], "N", "S", 2)
            lon = deg_min_header(e["longitude"], "E", "W", 3)
            fout.write(f"{date + tme}{lat}{lon} {' ' * 90}L{0.0:3.2f}{' ' * 9}{eid:>10}L\n")

            sub = picks[picks["event_index"] == eid]
            for (sid, fam), grp in sub.groupby(["station_id", "instrument_family"]):
                sta_name = group_alias[sid]
                net = "ZZ"  # alias encodes original network/station/location without truncation
                chan = z_channel(fam)
                used_sta_chan.add((sta_name, net, chan))

                p_rows = grp[grp["phase_type"] == "P"].sort_values("phase_score", ascending=False)
                s_rows = grp[grp["phase_type"] == "S"].sort_values("phase_score", ascending=False)

                tp_code = " "
                w_p = None
                ref = None
                if len(p_rows):
                    pk = p_rows.iloc[0]
                    w_p = prob_to_wcode(float(pk["phase_score"]))
                    if w_p is not None:
                        pol = float(pk["polarity_score"]) if pd.notna(pk["polarity_score"]) else 0.0
                        pol_l = "U" if pol > POL_MIN_SCORE else ("D" if pol < -POL_MIN_SCORE else " ")
                        pdate, ptime = split_dt(pk["phase_time"])
                        tp_code = f"IP{pol_l}{w_p}{pdate}{ptime[:4]} {ptime[4:]}"
                        ref = pk["phase_time"]
                    else:
                        n_dropped_w += 1
                if len(s_rows):
                    sk = s_rows.iloc[0]
                    w_s = prob_to_wcode(float(sk["phase_score"]))
                else:
                    w_s = None
                if w_p is None and (w_s is None or not len(s_rows)):
                    continue
                if ref is None and len(s_rows):
                    ref = s_rows.iloc[0]["phase_time"]
                if w_p is None:  # P dropped/absent: blank P field, date from S
                    sdate, stime = split_dt(ref)
                    tp_code = f"{' ':4}{sdate}{stime[:4]} {' ':4}"

                if len(s_rows) and w_s is not None:
                    # S seconds measured from the P (or reference) minute
                    sk = s_rows.iloc[0]
                    ref_min = ref.replace(second=0, microsecond=0)
                    ts_sec = int(round(100 * (sk["phase_time"] - ref_min).total_seconds()))
                    ts_code = f"{ts_sec:>4}ES {w_s}"
                else:
                    ts_code = " " * 8
                    if len(s_rows) and w_s is None:
                        n_dropped_w += 1

                fout.write(f"{sta_name:<5}{net}  {chan} {tp_code}{' ' * 7} {ts_code} \n")
                n_lines += 1
            fout.write("\n")  # mandatory event terminator

    with open(out / "input" / "stations.sta", "w") as f:
        # HYPOINVERSE station format #2 (manual v1.40 col table):
        # 1-5 sta | 7-8 net | 10 1-letter comp | 11-13 chan | 15 weight(blank=full)
        # 16-17 latdeg | 19-25 latmin F7.4 | 26 N/S | 27-29 londeg | 31-37 lonmin | 38 E/W
        # 39-42 elev I4(m) | 43-45 period F3.1 | 50+ delays/mag-corr
        for sta_name, net, chan in sorted(used_sta_chan):
            r = aliases[sta_name]["coordinates"]
            lat_abs, lon_abs = abs(r["latitude"]), abs(r["longitude"])
            latd, latm = int(lat_abs), 60.0 * (lat_abs - int(lat_abs))
            lond, lonm = int(lon_abs), 60.0 * (lon_abs - int(lon_abs))
            if round(latm, 4) >= 60: latd, latm = latd + 1, 0.0
            if round(lonm, 4) >= 60: lond, lonm = lond + 1, 0.0
            if not -999 <= r["elevation_m"] <= 9999: raise ValueError("Elevation exceeds native I4 field")
            latL = "N" if r["latitude"] >= 0 else "S"
            lonL = "E" if r["longitude"] >= 0 else "W"
            f.write(f"{sta_name:<5} {net:<2}  {chan:<3}  "
                    f"{latd:02d} {latm:7.4f}{latL}{lond:03d} {lonm:7.4f}{lonL}"
                    f"{r['elevation_m']:4.0f}{1.0:5.1f}   0.00  0.00  0.00\n")

    cre2crh(args.vp_model, out / "input" / "p.crh", "REGIONAL P")
    s_model = bool(args.vs_model)
    if s_model:
        cre2crh(args.vs_model, out / "input" / "s.crh", "REGIONAL S")

    (out / "input" / "conversion_meta.json").write_text(json.dumps({
        "s_model": s_model, "pos": args.pos, "n_phase_lines": n_lines,
        "n_events": len(events), "picks_dropped_no_station": n_no_sta,
        "picks_dropped_low_prob": n_dropped_w,
        "converter_sha256": __import__("hashlib").sha256(
            Path(__file__).read_bytes()).hexdigest()}, indent=2))
    print(f"phase.dat: {len(events)} events, {n_lines} phase lines "
          f"(no-station: {n_no_sta}, low-prob dropped: {n_dropped_w}); "
          f"station lines: {len(used_sta_chan)}; s_model={s_model}")


if __name__ == "__main__":
    main()
