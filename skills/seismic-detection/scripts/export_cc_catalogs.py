#!/usr/bin/env python3
"""Export CC >= 0.4/0.6/0.8 views from ONE globally associated MESS run.

Preserves event IDs and observations. Each view has its own phase/native files
and contract. Template reference events needed by retained dt.cc pairs are
listed separately, without counting them as threshold-qualified detections.
"""
import argparse
import csv
import json
import math
import os
import shutil
import fcntl
from datetime import datetime, timezone
from pathlib import Path

from contract_io import load_contract, product_path, sha256, relative
from pipeline_contracts import write_v2, now
from mess_contracts import load_mess_contracts

THRESHOLDS = (0.4, 0.6, 0.8)
LABELS = ("cc_0p4", "cc_0p6", "cc_0p8")


def rows(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def utc(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


def phase_blocks(path):
    result, current = {}, None
    for line in Path(path).read_text().splitlines(True):
        if not line.strip():
            continue
        values = next(csv.reader([line]))
        try:
            utc(values[0])
            event = int(values[5])
        except (ValueError, IndexError):
            if current is None:
                raise ValueError("Phase row without event header")
            result[current].append(line)
        else:
            if event in result:
                raise ValueError("Duplicate phase event ID")
            current = event
            result[event] = [line]
    return result


def native_events(path):
    result = {}
    for line in Path(path).read_text().splitlines(True):
        if not line.strip():
            continue
        event = int(line.split()[-1])
        if event in result:
            raise ValueError("Duplicate native event ID")
        result[event] = line
    return result


def differential_blocks(path):
    result, seen, current = [], set(), None
    for line in Path(path).read_text().splitlines(True):
        if not line.strip():
            continue
        if line.startswith("#"):
            values = line.split()
            pair = (int(values[1]), int(values[2]))
            key = tuple(sorted(pair))
            if key in seen or pair[0] == pair[1]:
                raise ValueError("Duplicate or self-referencing differential pair")
            seen.add(key)
            current = [pair, [line]]
            result.append(current)
        elif current is None:
            raise ValueError("Differential observation without pair header")
        else:
            current[1].append(line)
    return result


def template_records(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        first = line.split(",")[0]
        if "_" in first:
            event = int(first.split("_", 1)[0])
            if event in result:
                raise ValueError("Duplicate template ID")
            values = next(csv.reader([line]))
            if len(values) < 6:
                raise ValueError("Incomplete template event record")
            result[event] = (utc(values[1]), *map(float, values[2:6]))
    return result


def reference_event_line(event, record, depth_offset):
    origin, lat, lon, depth, magnitude = record
    clock = origin.strftime("%H%M%S") + f"{origin.microsecond // 10000:02d}"
    return (f"{origin:%Y%m%d}  {clock}   {lat:7.4f}   {lon:8.4f}   "
            f"{depth + depth_offset:8.3f}  {magnitude:4.2f}   0.00    0.00   0.0 {event:>10}\n")


def build_export(scan_manifest, output):
    scan_manifest, output = Path(scan_manifest).resolve(), Path(output).resolve()
    manifest = json.loads(scan_manifest.read_text())
    if manifest["workflow"] != "single_medium_library" or manifest["state"] != "ASSOCIATED":
        raise ValueError("A completed single-medium-library association is required")
    if manifest["template_source_tier"] != "medium" or manifest["catalog_cc_thresholds"] != list(THRESHOLDS):
        raise ValueError("Unexpected template source or final thresholds")
    inputs = {}
    for key, entry in manifest["files"].items():
        path = (scan_manifest.parent / entry["path"]).resolve()
        if sha256(path) != entry["sha256"]:
            raise ValueError("Scan artifact changed: " + key)
        inputs[key] = path
    catalogs = rows(inputs["catalog"])
    ids = [int(r["event_id"]) for r in catalogs]
    if len(ids) != len(set(ids)):
        raise ValueError("Source association has duplicate event IDs")
    for row in catalogs:
        score = float(row["best_detection_cc"])
        if not math.isfinite(score) or not 0 <= score <= 1 + 1e-6:
            raise ValueError("Invalid normalized detection CC")
    phases, events = phase_blocks(inputs["phase"]), native_events(inputs["event"])
    pairs, templates = differential_blocks(inputs["dt_cc"]), template_records(inputs["templates"])
    if set(phases) != set(ids) or not set(ids).issubset(events):
        raise ValueError("Catalog, phase and native event IDs disagree")
    for event in {event for pair, _ in pairs for event in pair} - set(events):
        if event not in templates:
            raise ValueError("dt.cc refers to a missing event that is not a template reference")
        events[event] = reference_event_line(event, templates[event], float(manifest["hypodd_depth_offset_km"]))

    chain = load_mess_contracts(manifest["contracts"]["preprocess"], manifest["contracts"]["relocation"],
                                location=manifest["contracts"]["location"],
                                association=manifest["contracts"].get("association"))
    sources = {stage: chain[stage] for stage in ("preprocess", "relocation", "location")}
    medium = product_path(sources["relocation"][1], "relocation", "outputs.catalogs.medium")
    medium_ids = {int(r["event_id"][2:] if r["event_id"].startswith("gm") else r["event_id"]) for r in rows(medium)}
    if not set(templates).issubset(medium_ids):
        raise ValueError("Template IDs are not drawn exclusively from the HypoDD medium catalog")
    known = rows(product_path(sources["location"][1], "location", "outputs.catalog_path"))
    known_times = []
    from datetime import timedelta
    for row in known:
        t = datetime.strptime(row["date"], "%Y/%m/%d %H:%M").replace(tzinfo=timezone.utc)
        known_times.append((t + timedelta(seconds=float(row["sec"])), row["event_id"]))
    for row in catalogs:
        self_detection = int(row["self_detection"]) == 1
        if self_detection and int(row["event_id"]) not in templates:
            raise ValueError("Self-detection ID is absent from the template library")
        matches = [event for t, event in known_times if abs((utc(row["origin_time"]) - t).total_seconds()) < 2]
        row["status"] = "known" if self_detection or matches else "new"
        row["known_match_method"] = "template_identity" if self_detection else ("time_window" if matches else "none")
        row["location_method"] = "template_inherited"
        row["magnitude_type"] = "uncalibrated_relative"
    header = list(catalogs[0]) if catalogs else ["origin_time", "latitude", "longitude", "depth_km", "magnitude",
        "event_id", "template_count", "best_detection_cc", "self_detection", "status", "known_match_method", "location_method", "magnitude_type"]
    index = {"workflow": "single_medium_library", "run_id": manifest["run_id"],
             "template_source_tier": "medium", "catalog_cc_thresholds": list(THRESHOLDS),
             "source_scan_manifest_sha256": sha256(scan_manifest), "catalogs": {}}
    output.mkdir(parents=True, exist_ok=True)
    for threshold, label in zip(THRESHOLDS, LABELS):
        directory = output / label
        directory.mkdir()
        selected = [r for r in catalogs if float(r["best_detection_cc"]) >= threshold]
        selected_ids = {int(r["event_id"]) for r in selected}
        kept_pairs = [(pair, lines) for pair, lines in pairs
                      if (pair[0] in selected_ids or pair[1] in selected_ids)
                      and all(event in selected_ids or event in templates for event in pair)]
        references = {event for pair, _ in kept_pairs for event in pair} - selected_ids
        native_ids = selected_ids | references
        for filename, data in (("catalog.csv", selected), ("new_events.csv", [r for r in selected if r["status"] == "new"])):
            with (directory / filename).open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=header)
                writer.writeheader()
                writer.writerows(data)
        (directory / "phase.csv").write_text("".join(line for event in ids if event in selected_ids for line in phases[event]))
        (directory / "event.dat").write_text("".join(line for event, line in events.items() if event in native_ids))
        (directory / "dt.cc").write_text("".join(line for _, lines in kept_pairs for line in lines))
        (directory / "reference_events.json").write_text(json.dumps({"event_ids": sorted(references),
            "role": "Template reference events for retained differential times; excluded from detection counts."}, indent=2) + "\n")
        stats = {"after_dedup": len(selected), "new_events": sum(r["status"] == "new" for r in selected),
                 "phase_events": len(selected_ids), "native_events": len(native_ids),
                 "reference_events": len(references), "differential_pairs": len(kept_pairs)}
        (directory / "qc.json").write_text(json.dumps({"cc_min": threshold, **stats,
            "event_ids_unique": True, "native_references_resolved": True,
            "waveform_review": "NOT_TESTED", "location_validation": "NOT_TESTED"}, indent=2) + "\n")
        artifacts = {}
        def register(role, path):
            path = Path(path).resolve()
            ref = relative(path, directory)
            artifacts[role] = {"path": ref, "kind": "file", "required": True, "sha256": sha256(path)}
            return ref
        upstream = [{"stage": stage, "contract_path": register("upstream_" + stage, source),
                     "input_verification": "PASS", "verification_basis": "contract_artifact_checks"}
                    for stage, (_, source) in sources.items()]
        doc = {"contract_version": "2.1", "stage": "detection", "software": {"name": "PALM MESS", "version": manifest["palm_commit"]},
            "run_id": manifest["run_id"] + ":" + label, "created_at": now(), "upstream": upstream,
            "status": "READY", "workflow": "single_medium_library", "qc_path": register("qc", directory / "qc.json"),
            "template_source": {"contract_path": relative(sources["relocation"][1], directory),
                "catalog_path": register("medium_catalog", medium), "tier": "medium",
                "event_selection_rule": "HypoDD medium catalog; min_snr=2, min_sta=4"},
            "template_processing": {"compatible_with_preprocess_contract": True, **manifest["processing"]},
            "scan": {"threshold": {"kind": "fixed_cc", "value": 0.3}, "min_stations": 4},
            "selection": {"cc_min": threshold, "score_field": "best_detection_cc", "operator": ">="},
            "dedup": {"rule": "Single-library global association; independent threshold views without cross-view merge", "against_known_catalog": True},
            "outputs": {"detections_path": register("detections", directory / "catalog.csv"),
                "new_events_path": register("new_events", directory / "new_events.csv"), "schema": header,
                "phase_path": register("phase", directory / "phase.csv"),
                "event_path": register("event", directory / "event.dat"),
                "dt_cc_path": register("dt_cc", directory / "dt.cc"),
                "reference_events_path": register("reference_events", directory / "reference_events.json")},
            "stats": stats, "artifacts": artifacts,
            "warnings": ["Positions inherit template locations; magnitudes are uncalibrated relative values.",
                         "Time-window catalog matches do not establish event identity; candidate waveform review remains required.",
                         "Native input references were checked; HypoDD relocation and the depth-offset interpretation were not run here."]}
        register("source_scan_manifest", scan_manifest)
        for name, path in inputs.items():
            register("source_" + name, path)
        written = write_v2(doc, directory / "contract.v2.json")
        if written["validation"]["artifact_status"] != "PASS":
            raise ValueError("Exported catalog failed artifact verification")
        index["catalogs"][label] = {"cc_min": threshold, "contract_path": label + "/contract.v2.json", **stats}
    (output / "catalogs.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    return index


def completed_output(output, scan_manifest):
    index = json.loads((output / "catalogs.json").read_text())
    if set(index["catalogs"]) != set(LABELS):
        raise ValueError("Incomplete three-catalog index")
    for label, threshold in zip(LABELS, THRESHOLDS):
        doc, path = load_contract(output / label, "detection")
        artifact = doc["artifacts"]["source_scan_manifest"]
        if (path.parent / artifact["path"]).resolve() != scan_manifest or artifact["sha256"] != sha256(scan_manifest):
            raise ValueError("Existing catalogs belong to a different source scan")
        if doc["selection"]["cc_min"] != threshold:
            raise ValueError("Existing catalog threshold differs")
    return index


def compatible_partial(output, pending):
    """Adopt legacy partial output only when each existing file matches this export."""
    for path in output.rglob("*"):
        relative_path = path.relative_to(output)
        expected = pending / relative_path
        if path.is_symlink() or not expected.exists() or path.is_dir() != expected.is_dir():
            raise ValueError("Unrecognized partial export content: " + str(path))
        if path.is_file():
            if path.name == "contract.v2.json":
                old, new = json.loads(path.read_text()), json.loads(expected.read_text())
                old.pop("created_at", None)
                new.pop("created_at", None)
                if old != new:
                    raise ValueError("Partial contract belongs to different inputs")
            elif path.name == "catalogs.json":
                old, new = json.loads(path.read_text()), json.loads(expected.read_text())
                old.pop("source_scan_manifest_sha256", None)
                new.pop("source_scan_manifest_sha256", None)
                if old != new:
                    raise ValueError("Partial catalog index belongs to different inputs")
            elif path.read_bytes() != expected.read_bytes():
                raise ValueError("Partial output differs from this scan: " + str(path))


def export(scan_manifest, output):
    scan_manifest, output = Path(scan_manifest).resolve(), Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    pending = output.with_name("." + output.name + ".pending")
    with output.with_name("." + output.name + ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        complete = (output / "catalogs.json").is_file() and all(
            (output / label / "contract.v2.json").is_file() for label in LABELS)
        if complete:
            return completed_output(output, scan_manifest)
        state = {"protocol": "mess-export-atomic-v1", "target": str(output),
                 "source_sha256": sha256(scan_manifest)}
        if pending.exists():
            marker = pending / ".export_state.json"
            if not marker.is_file():
                raise ValueError("Unowned pending export directory")
            previous = json.loads(marker.read_text())
            if previous.get("protocol") != state["protocol"] or previous.get("target") != str(output):
                raise ValueError("Pending export ownership differs")
            shutil.rmtree(pending)
        pending.mkdir()
        (pending / ".export_state.json").write_text(json.dumps(state, sort_keys=True) + "\n")
        result = build_export(scan_manifest, pending)
        if sha256(scan_manifest) != state["source_sha256"]:
            raise ValueError("Scan manifest changed during export")
        completed_output(pending, scan_manifest)
        if output.exists():
            compatible_partial(output, pending)
            shutil.rmtree(output)
        os.replace(pending, output)
        return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scan-manifest", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    print(json.dumps(export(args.scan_manifest, args.out), indent=2))


if __name__ == "__main__":
    main()
