#!/usr/bin/env python3
"""Publish completed independent HypoDD tiers, retaining native IDs and times."""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from contract_io import load_contract, product_path, publish_payload
from damping_metrics import load_catalog, displacement_metrics
from tier_outcomes import outcome, sha

FIELDS = ["id", "lat", "lon", "dep", "x", "y", "z", "ex", "ey", "ez", "yr", "mo", "dy", "hr", "mi", "sc",
          "mag", "nccp", "nccs", "nctp", "ncts", "rcc", "rct", "cid"]


def read_native(path):
    frame = pd.read_csv(path, sep=r"\s+", header=None, names=FIELDS)
    frame["event_id"] = frame.id.astype(int).map(lambda i: f"gm{i:06d}")
    frame["time"] = [pd.Timestamp(year=int(r.yr), month=int(r.mo), day=int(r.dy), hour=int(r.hr),
                                   minute=int(r.mi), tz="UTC") + pd.Timedelta(seconds=float(r.sc))
                       for r in frame.itertuples()]
    return frame.drop(columns=["mag"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--location-dir", required=True)
    ap.add_argument("--vp-model", required=True)
    ap.add_argument("--ratio", type=float, required=True)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()
    work = Path(args.workdir).resolve()
    _, location = load_contract(args.location_dir, "location")
    initial = pd.read_csv(product_path(location, "location", "outputs.catalog_path"))
    mapping = initial[["event_id"]].copy()
    sets, stats, catalog_paths, reloc_paths, tier_states, curves = {}, {}, {}, {}, {}, {}
    for tier in ("loose", "medium", "strict"):
        directory = work / tier
        try:
            state = outcome(directory)
        except (OSError, ValueError, KeyError) as exc:
            state = {"status": "UNAVAILABLE", "reason": "INVALID_EVIDENCE: " + str(exc), "damp": None}
        tier_states[tier] = state
        curve = directory / "qc/damping_trials.png"
        if curve.is_file():
            curves[tier] = str(curve)
        if state["status"] == "UNAVAILABLE":
            mapping["relocated_" + tier] = pd.Series(pd.NA, index=mapping.index, dtype="boolean")
            stats[tier] = {**state, "events": None, "scientific_status": "NOT_TESTED"}
            continue
        if state["status"] == "READY":
            selection = json.loads((directory / "qc/damping_selection.json").read_text())
            if selection["context"]["vp_model_sha256"] != sha(args.vp_model) or selection["context"]["ratio"] != args.ratio:
                raise ValueError("Published model/ratio differs from the tier's actual experiment")
            catalog = read_native(directory / "output/hypoDD.reloc")
            reloc_paths[tier] = str(directory / "output/hypoDD.reloc")
            metrics = displacement_metrics(load_catalog(directory / "output/hypoDD.loc"), load_catalog(directory / "output/hypoDD.reloc"))
        else:
            catalog = pd.DataFrame(columns=[c for c in FIELDS if c != "mag"] + ["event_id", "time"])
            metrics = None
        if catalog.event_id.duplicated().any() or not set(catalog.event_id).issubset(set(initial.event_id)):
            raise ValueError("Relocation IDs differ from location")
        path = work / ("catalog_" + tier + ".csv")
        catalog.to_csv(path, index=False, date_format="%Y-%m-%dT%H:%M:%S.%fZ")
        catalog_paths[tier] = str(path)
        sets[tier] = set(catalog.event_id)
        mapping["relocated_" + tier] = mapping.event_id.isin(sets[tier])
        stats[tier] = {**state, "events": len(catalog), "spatial_metrics": metrics, "scientific_status": "NOT_TESTED"}
    if not catalog_paths:
        raise ValueError("All tiers are unavailable; no successful or verified-empty delivery exists")
    mapping.to_csv(work / "event_lineage.csv", index=False)
    qc_dir = work / "qc"
    qc_dir.mkdir(exist_ok=True)
    (qc_dir / "tier_comparison.json").write_text(json.dumps(stats, indent=2) + "\n")
    (qc_dir / "set_diffs.json").write_text(json.dumps({
        "common": sorted(set.intersection(*sets.values())),
        "differences": {a + "_minus_" + b: sorted(sets[a] - sets[b]) for a in sets for b in sets if a != b}}, indent=2) + "\n")
    import matplotlib
    matplotlib.use("agg")
    import matplotlib.pyplot as plt
    fig, axis = plt.subplots(figsize=(6, 4))
    axis.bar(list(stats), [s["events"] if s["events"] is not None else float("nan") for s in stats.values()])
    for index, state in enumerate(stats.values()):
        if state["events"] is None: axis.text(index, 0, "unavailable", ha="center")
    axis.set(ylabel="Retained events", title="Independent parameter tiers")
    fig.tight_layout()
    fig.savefig(qc_dir / "tier_comparison.png", dpi=140)
    plt.close(fig)
    payload = {"contract_version": "1.0", "stage": "relocation", "run_id": args.run_id,
        "created_at": datetime.now(timezone.utc).isoformat(), "software": {"name": "ph2dt + HypoDD", "version": "pinned"},
        "upstream": [{"stage": "location", "contract_path": str(location), "input_verification": "PASS"}],
        "status": "READY" if all(s["status"] == "READY" for s in tier_states.values()) else "PARTIAL", "qc_path": str(qc_dir),
        "pairing": {"tier_minlinks": {"loose": 3, "medium": 4, "strict": 6}},
        "times": {"catalog_dt": True, "cross_correlation": False},
        "solver": {"velocity_model": {"file": str(Path(args.vp_model).resolve()), "vp_vs_ratio": args.ratio},
                   "selected_damp_by_tier": {t: stats[t]["damp"] for t in stats}, "trial_curve_paths": curves},
        "tiers": {"paths": catalog_paths, "statuses": tier_states, "definitions": {"loose": "MINLNK/MINOBS/OBSCT 3; WDCT last 4 km",
                   "medium": "MINLNK/MINOBS/OBSCT 4; WDCT last 3 km", "strict": "MINLNK/MINOBS/OBSCT 6; WDCT last 2 km"}},
        "outputs": {"event_mapping_path": str(work / "event_lineage.csv"), "reloc_paths": reloc_paths},
        "stats": {"events_relocated": len(set.union(*sets.values())), "orphans": 0},
        "warnings": ["Relative catalog differences and LSQR residuals do not establish depth accuracy. Inspect each tier's lost events and airquakes."]}
    # Orphans are locations never entering a ph2dt selection in any tier.
    paired = set()
    pairing_complete = True
    for tier in tier_states:
        if tier_states[tier]["status"] == "UNAVAILABLE":
            pairing_complete = False
            continue
        selection_file = work / tier / "input/event.sel"
        if not selection_file.is_file():
            if tier_states[tier]["status"] != "EMPTY": pairing_complete = False
            continue
        try:
            selected = {f"gm{int(line.split()[-1]):06d}" for line in selection_file.read_text().splitlines() if line.strip()}
            if not selected.issubset(set(initial.event_id)):
                pairing_complete = False
            else:
                paired.update(selected)
        except (OSError, ValueError):
            pairing_complete = False
    payload["stats"]["orphans"] = len(set(initial.event_id) - paired) if pairing_complete else None
    actual_parameters = {}
    for tier in tier_states:
        entry = {"pairing": None, "solver": None}
        inp = work / tier / "ph2dt.inp"
        if inp.is_file():
            lines = [l for l in inp.read_text().splitlines() if l.strip() and not l.lstrip().startswith("*")]
            values = list(map(float, lines[-1].split()))
            entry["pairing"] = dict(zip(["minwght","maxdist","maxsep","maxngh","minlnk","minobs","maxobs"], values))
        selected = work / tier / "qc/damping_selection.json"
        if selected.is_file():
            ctx = json.loads(selected.read_text())["context"]
            entry["solver"] = {k: ctx[k] for k in ["obsct","wdct_last","dist","ratio"]}
        actual_parameters[tier] = entry
    payload["pairing"] = {"actual_parameters_by_tier": actual_parameters}
    payload["tiers"]["definitions"] = {t: json.dumps(v, sort_keys=True) for t,v in actual_parameters.items()}
    contract = publish_payload(payload, work / "contract.v2.json", "relocation")
    print(json.dumps({"tier_counts": {t: stats[t]["events"] for t in stats}, "validation": contract["validation"]}))


if __name__ == "__main__":
    main()
