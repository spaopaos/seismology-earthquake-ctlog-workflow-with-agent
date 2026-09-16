#!/usr/bin/env python3
"""Adapt our preprocess archive to PALM v5 layout + build template library (R1).

Two jobs:
  1) archive (per-station-group-day Z/N/E files) -> PALM data layout
     (data_dir/YYYYMMDD/net.sta.chn per-component files), with a processing
     fingerprint manifest (R8/fingerprint rule);
  2) HypoDD medium catalog only -> PALM template phase file (.temp):
     event line "id_name,ot,lat,lon,dep,mag", station lines "net.sta,tp,ts".

v1.3 fixes (from the 2026-09-12 GLM run's real findings):
  - contract structure: real archive contract nests under data_contract
    (target_band_hz / archive_component_labels); manifest columns are file_Z/N/E
  - event id_name must be >=14 chars AND have a unique suffix (it doubles as the
    template storage name): use {eid}_{YYYYMMDDHHMMSSmmm}_{eid} (PALM 1_select style)
  - station rows without an S pick are dropped AND counted (trailing empty ts
    crashes UTCDateTime; MESS templates need P+S)

No re-filtering of the archive (contract forbids). Derived copies at other
sampling rates (Nyquist path B) are written separately and fingerprinted.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from contract_io import load_contract, product_path, archive_fingerprint
from mess_contracts import load_mess_contracts


def fingerprint(contract):
    return archive_fingerprint(contract)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--relocation-dir", required=True, help="Contract supplying outputs.catalogs.medium")
    ap.add_argument("--association-dir", required=True, help="Contract supplying events and assigned picks")
    ap.add_argument("--out", required=True)
    ap.add_argument("--time-range", help="YYYYMMDD-YYYYMMDD, right endpoint excluded")
    args = ap.parse_args()
    chain = load_mess_contracts(args.archive, args.relocation_dir, association=args.association_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    contract, archive_file = load_contract(args.archive, "preprocess")
    archive_base = archive_file.parent
    fp = fingerprint(contract)
    (out / "data_fingerprint.json").write_text(json.dumps(fp, indent=2))

    # Template observations and scan days both contribute to the waveform view.
    medium_path = product_path(args.relocation_dir, "relocation", "outputs.catalogs.medium")
    cat = pd.read_csv(medium_path)
    if "time" not in cat:
        raise ValueError("Medium catalog must carry native origin times")
    cat["time"] = pd.to_datetime(cat["time"], utc=True)
    picks = pd.read_csv(product_path(chain["association"][1], "association", "outputs.assignments_path"))
    picks["phase_time"] = pd.to_datetime(picks["phase_time"], utc=True)
    picks = picks[picks["event_index"].isin(cat.event_id.str.removeprefix("gm").astype(int))]
    template_dates = set()
    for when in list(cat.time) + list(picks.phase_time):
        if pd.isna(when):
            raise ValueError("Missing template origin or phase time")
        for offset in (-1, 0, 1):
            template_dates.add((when + pd.Timedelta(days=offset)).strftime("%Y-%m-%d"))
    scan_dates = set()
    if args.time_range:
        start, end = args.time_range.split("-")
        first, last = pd.Timestamp(start), pd.Timestamp(end)
        if first >= last:
            raise ValueError("Scan date range must increase")
        scan_dates = {d.strftime("%Y-%m-%d") for d in pd.date_range(first - pd.Timedelta(days=1), last)}
    data_dir = out / "continuous"
    n_linked = 0
    manifest = product_path(args.archive, "preprocess", "manifest_path")
    df = pd.read_csv(manifest)
    df = df.loc[df.status.isin(["READY", "PARTIAL_DAY"])].copy()
    if not args.time_range:
        scan_dates = set(df.date)
    df = df.loc[df.date.isin(template_dates | scan_dates)].copy()
    df["physical"] = df.group.str.split(".").str[:2].str.join(".")
    counts = df.groupby(["physical", "group"]).size().reset_index(name="days")
    counts["family_priority"] = counts.group.str.split(".").str[-1].map({"HH": 0, "SH": 1, "HN": 2}).fillna(3)
    chosen = counts.sort_values(["physical", "days", "family_priority", "group"], ascending=[True, False, True, True]).drop_duplicates("physical")
    selected_groups = dict(zip(chosen.physical, chosen.group))
    df = df.loc[df.group.isin(chosen.group)]
    effective_bands = {}
    for row in df.to_dict("records"):
        metadata = json.loads((archive_base / row["metadata"]).read_text())
        band = tuple(metadata["analysis_band_hz"])
        if row["group"] in effective_bands and effective_bands[row["group"]] != band:
            raise ValueError("Template and scan days have different effective bands for " + row["group"])
        effective_bands[row["group"]] = band
    links = []
    for row in df.to_dict("records"):
        day = str(row["date"]).replace("-", "")
        for comp in ("E", "N", "Z"):
            value = row["file_" + comp]
            if not isinstance(value, str) or not value:
                raise ValueError("Missing component in a selected archive group")
            src = (archive_base / value).resolve()
            if not src.is_file():
                raise ValueError("Selected archive file is missing: " + str(src))
            parts = row["group"].split(".")
            dst = data_dir / day / f"{parts[0]}.{parts[1]}.{parts[3]}{comp}"
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_symlink() and dst.resolve() != src:
                raise ValueError("Existing continuous view points to a different instrument")
            if not dst.exists():
                dst.symlink_to(src)
            links.append({"source": str(src), "view": str(dst), "group": row["group"], "date": row["date"], "component": comp})
            n_linked += 1
    (out / "continuous_manifest.json").write_text(json.dumps({"selection_rule": "one fixed instrument group per physical station: maximum available days, then HH/SH/HN", "selected_groups": selected_groups, "template_dates": sorted(template_dates), "scan_dates": sorted(scan_dates), "files": links}, indent=2) + "\n")

    # --- template phase file (.temp) ---
    n_temp_events = 0
    n_dropped_no_s = 0
    with open(out / "templates.temp", "w") as f:
        for _, e in cat.iterrows():
            eid_str = str(e["event_id"])
            eid = int(eid_str.replace("gm", ""))
            ot = e["time"]
            if pd.isna(ot):
                raise ValueError(f"{eid_str} missing native relocation origin time")
            # id_name: >=14 chars, unique suffix doubles as storage name (PALM rule)
            id_name = f"{eid}_{ot.strftime('%Y%m%d%H%M%S')}{int(ot.microsecond/1e3):03d}_{eid}"
            assert len(id_name) >= 14
            lat = e["latitude"] if "latitude" in e else e["lat"]
            lon = e["longitude"] if "longitude" in e else e["lon"]
            dep = e["depth_km"] if "depth_km" in e else e.get("dep", 0)
            origin_text = ot.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            f.write(f"{id_name},{origin_text},{lat},{lon},{dep},0.0\n")
            sub = picks[(picks["event_index"] == eid) & picks["station_id"].isin(selected_groups.values())]
            for group_id, g in sub.groupby("station_id"):
                physical = ".".join(group_id.split(".")[:2])
                p_ = g[g["phase_type"] == "P"]
                s_ = g[g["phase_type"] == "S"]
                if len(p_) == 0 or len(s_) == 0:
                    n_dropped_no_s += len(p_) if len(s_) == 0 else 0
                    continue  # MESS templates need P+S; drop S-less rows and count
                tp = p_["phase_time"].iloc[0]
                ts = s_["phase_time"].iloc[0]
                f.write(f"{physical},{tp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')},{ts.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}\n")
            n_temp_events += 1

    (out / "template_source.json").write_text(json.dumps({
        "tier": "medium", "catalog_path": str(medium_path), "candidate_events": n_temp_events,
        "selected_instrument_groups": selected_groups,
        "origin_time_source": "HypoDD medium native origin time",
        "station_rows_dropped_no_s": n_dropped_no_s, "linked_component_files": n_linked,
    }, indent=2) + "\n")
    print(f"linked {n_linked} component-day files; template events: {n_temp_events}; "
          f"station rows dropped (no S): {n_dropped_no_s}")


if __name__ == "__main__":
    main()
