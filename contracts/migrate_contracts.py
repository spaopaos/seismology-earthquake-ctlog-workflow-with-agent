"""Explicit migration of known stage payloads to v2; never edits scientific products.

Existing contracts stay in place. A source hash and revision timestamp identify
the metadata revision, without claiming a new scientific run or new scientific PASS.
"""
import argparse
import copy
import json
from pathlib import Path

from pipeline_contracts import (ROOT, NAMES, VERSION, columns, csv_rows, now, relative,
                                sha256, write_v2, supported_version, contract_file)

def normalize(source, stage):
    source = Path(source).resolve()
    base = source.parent
    old = json.loads(source.read_text())
    if old.get("template_only"):
        raise ValueError("A template is not a completed run and cannot be published")
    if old.get("stage") and old["stage"] != stage:
        raise ValueError("Payload stage differs from the requested publication stage")
    if supported_version(old):
        return copy.deepcopy(old)
    if stage == "detection":
        raise ValueError("The old multi-library detection workflow is retired; publish single-medium CC catalogs with contract version 2.1")
    if str(old.get("contract_version", "")).startswith("2."):
        raise ValueError("Unsupported contract revision")
    doc = copy.deepcopy(old)
    notes = []
    doc.update(contract_version=VERSION, stage=stage, artifacts={})
    stamp = old.get("created_at")
    doc["created_at"] = stamp if isinstance(stamp, str) and "T" in stamp else now()
    doc["run_id"] = old.get("run_id") or "legacy-" + stage + "-" + sha256(source)[:12]
    doc["software"] = old.get("software", {"name": "ObsPy preprocessing", "version": None})
    doc["warnings"] = list(old.get("warnings", []))
    doc["provenance"] = {
        "source_contract_path": source.name, "source_contract_sha256": sha256(source),
        "source_contract_version": old.get("contract_version", old.get("contract_schema_version")),
        "source_created_at": old.get("created_at", old.get("generated")),
        "revision_created_at": now(), "notes": notes,
    }
    notes.append("Metadata normalization and file checks only; existing scientific verification claims retain their original scope.")
    if "run_id" not in old:
        notes.append("The legacy record has no run_id; the deterministic ID identifies that record, not a reconstructed execution time.")

    def locate(value, fallback=None):
        candidates = []
        if isinstance(value, str) and value.strip():
            clean = value.split(" (")[0].strip()
            candidates.extend([base / value, base / clean])
        if fallback is not None:
            candidates.append(base / fallback)
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()
        if fallback is not None:
            return (base / fallback).resolve()
        raise ValueError("Cannot resolve legacy path without evidence: " + str(value))

    def add(role, value, fallback=None, directory=False, required=True):
        path = locate(value, fallback)
        ref = relative(path, base)
        descriptor = {"path": ref, "kind": "directory" if directory or path.is_dir() else "file", "required": required}
        if path.is_file():
            descriptor["sha256"] = sha256(path)
        doc["artifacts"][role] = descriptor
        if isinstance(value, str) and value != ref:
            notes.append("Path %s: %r -> %r" % (role, value, ref))
        return ref

    add("source_contract", source.name)
    doc["status"] = old.get("status", {"PASS": "READY", "PASSED": "READY", "FAIL": "FAILED",
                                      "FAILED": "FAILED", "PARTIAL": "PARTIAL"}.get(
                                          old.get("archive_validation_status"), "PARTIAL"))
    if old.get("qc_path") or (base / "qc").is_dir():
        doc["qc_path"] = add("qc", old.get("qc_path"), "qc", directory=True)
    else:
        doc.pop("qc_path", None)
        if doc["status"] == "READY":
            doc["status"] = "PARTIAL"
        doc["warnings"].append("QC artifact not supplied; metadata revision cannot claim READY.")
    for key in ("config_path", "script_path"):
        if doc.get(key):
            doc[key] = add(key, doc[key])
        else:
            doc.pop(key, None)

    upstream, verification = [], []
    for index, item in enumerate(old.get("upstream", [])):
        name = item.get("stage", "").split(" ")[0]
        raw_status = item.get("input_verification", item.get("status", "NOT_TESTED"))
        status = raw_status.split(" ")[0] if isinstance(raw_status, str) else "NOT_TESTED"
        if status not in ("PASS", "FAIL", "NOT_TESTED"):
            status = "NOT_TESTED"
        if name in NAMES:
            previous = locate(item["contract_path"])
            if previous.is_dir():
                previous = contract_file(previous, name)
            current = previous.parent / "contract.v2.json"
            if not current.exists():
                candidate = json.loads(previous.read_text())
                if not supported_version(candidate):
                    raise ValueError("Migrate upstream first: " + str(previous))
                current = previous
            ref = add("upstream_" + name, str(current))
            upstream.append({"stage": name, "contract_path": ref, "input_verification": status,
                             "verification_basis": "source_record",
                             "verification_note": raw_status})
        else:
            evidence = []
            raw_path = item.get("contract_path")
            if raw_path and "(+medium/strict)" in raw_path:
                first = raw_path.split(" (")[0]
                candidates = [first.replace("loose/", tier + "/", 1) for tier in ("loose", "medium", "strict")]
            elif raw_path and " sec" not in raw_path:
                candidates = [raw_path]
            elif item.get("gate") == "phase_dat_verification":
                candidates = ["full/input/phase_dat_verification.json"]
            else:
                candidates = []
            for j, candidate in enumerate(candidates):
                path = base / candidate
                if path.is_file():
                    evidence.append(add("verification_%s_%s" % (index, j), candidate))
            verification.append({"name": item.get("stage", item.get("gate", "legacy_check")),
                "status": status if evidence else "NOT_TESTED", "evidence_paths": evidence,
                "basis": "source_record", "note": json.dumps(item, ensure_ascii=False)})
    doc["upstream"], doc["verification"] = upstream, verification
    outputs = old.get("outputs", {})

    if stage == "preprocess":
        for key in ("contract_schema_version", "generated", "template_only", "manifest_relative_path",
                    "effective_config_relative_path"):
            doc.pop(key, None)
        doc["archive_root"] = add("archive", ".", directory=True)
        doc["manifest_path"] = add("manifest", old.get("manifest_relative_path"), "daily_manifest.csv")
        doc["config_path"] = add("config", old.get("effective_config_relative_path"), "effective_config.json")
        effective = json.loads((base / doc["config_path"]).read_text())
        doc["software"] = {"name": "ObsPy preprocessing", "version": effective.get("versions", {}).get("obspy")}
        doc["archive_validation_status"] = {"PASSED": "PASS", "FAILED": "FAIL"}.get(
            old["archive_validation_status"], old["archive_validation_status"])
        rows = csv_rows(base / doc["manifest_path"])
        ready = sum(r["status"] == "READY" for r in rows)
        partial = sum(r["status"] == "PARTIAL_DAY" for r in rows)
        doc["stats"] = {"group_days": len(rows), "ready": ready, "partial": partial,
                        "unavailable": len(rows) - ready - partial}
    elif stage == "picking":
        doc["outputs"]["picks_path"] = add("picks", outputs["picks_path"])
        rows = csv_rows(base / doc["outputs"]["picks_path"])
        doc["outputs"]["schema"] = columns(base / doc["outputs"]["picks_path"])
        stats = doc.setdefault("stats", {})
        stats.update(n_p=sum(r["phase_type"].lower() == "p" for r in rows),
                     n_s=sum(r["phase_type"].lower() == "s" for r in rows))
    elif stage == "association":
        for key, role in (("events_path", "events"), ("assignments_path", "assignments")):
            doc["outputs"][key] = add(role, outputs[key])
        unused = old["stats"]["unassociated_picks_path"]
        doc["stats"]["unassociated_picks_path"] = add("unassociated", unused)
        doc["outputs"]["unassociated_picks_path"] = doc["stats"]["unassociated_picks_path"]
        doc["station_source"]["path"] = add("stations", old["station_source"]["path"])
        doc["params"]["rationale_path"] = add("rationale", old["params"]["rationale_path"])
        doc["params"].pop("dbscan_eps_km", None)
        vm = doc["velocity_model"]
        raw_parts = vm["path"].split(" + ")
        vm["p_path"] = add("vp_model", vm.get("p_path", raw_parts[0]))
        if vm.get("s_path") or len(raw_parts) > 1:
            vm["s_path"] = add("vs_model", vm.get("s_path", raw_parts[-1]),
                               str((base / vm["p_path"]).parent / raw_parts[-1]))
        vm["path"] = vm["p_path"]
        rows = csv_rows(base / doc["outputs"]["assignments_path"])
        unused_rows = csv_rows(base / doc["stats"]["unassociated_picks_path"])
        n_assoc = sum(int(r["event_index"]) >= 0 for r in rows)
        doc["outputs"]["assignment_layout"] = "all_picks" if n_assoc < len(rows) else "assigned_only"
        doc["stats"].update(picks_in=n_assoc + len(unused_rows), picks_associated=n_assoc,
                            n_events=len(csv_rows(base / doc["outputs"]["events_path"])))
        effective_path = base / "effective_config.json"
        if effective_path.is_file():
            effective = json.loads(effective_path.read_text())
            if effective.get("dbscan_eps") != doc["params"].get("dbscan_eps_s"):
                raise ValueError("Association contract eps differs from effective_config.json")
    elif stage == "location":
        inputs = doc.pop("inputs", {})
        doc["input_description"] = inputs
        out = {}
        for new, old_key, fallback in (("catalog_path", "catalog", "hyp_catalog.csv"),
            ("arc_path", "arc", "full/output/run.arc"), ("prt_path", "prt", "full/output/run.prt"),
            ("sum_path", "sum", "full/output/run.sum"), ("rejected_path", "rejected_list", "rejected_events.csv")):
            out[new] = add(new, outputs.get(new, outputs.get(old_key)), fallback)
        out["located_schema"] = columns(base / out["catalog_path"])
        doc["outputs"] = out
        run_base = (base / out["arc_path"]).parent.parent
        if (run_base / "input/station_aliases.json").is_file():
            out["station_aliases_path"] = add("station_aliases", str(run_base / "input/station_aliases.json"))
        p_path = add("p_model", str(run_base / "input/p.crh"))
        doc["model_file"] = {"p_path": p_path, "comparison_with_association": "NOT_TESTED",
            "comparison_note": "Common source model is reported, but representation equivalence is not established by this metadata migration."}
        if (run_base / "input/s.crh").exists():
            doc["model_file"]["s_path"] = add("s_model", str(run_base / "input/s.crh"))
        doc["station_file"] = {"path": add("station_file", str(run_base / "input/stations.sta")),
                               "generated_from": add("station_source", inputs.get("stations"), "../resp/sta.lst")}
        doc["phase_file"] = {"path": add("phase_file", str(run_base / "input/phase.dat")),
                             "generator": "seismic-location/make_hypoinverse_inputs.py (identity in original conversion_meta.json)"}
        stats = doc["stats"]
        stats["located"] = len(csv_rows(base / out["catalog_path"]))
        stats["rejected"] = len(csv_rows(base / out["rejected_path"]))
        stats["events_in"] = stats["located"] + stats["rejected"]
        for key in ("n_events_in", "n_located", "n_rejected"):
            stats.pop(key, None)
    elif stage == "relocation":
        paths = old.get("tiers", {}).get("paths", {})
        out = {"catalogs": {}, "reloc_paths": {}}
        union, counts = set(), {}
        for tier, value in paths.items():
            if (base / tier / "input/station_aliases.json").is_file():
                add("station_aliases_" + tier, str(base / tier / "input/station_aliases.json"))
            out["catalogs"][tier] = add("catalog_" + tier, value)
            native = outputs.get("reloc_paths")
            if native is None:
                out["reloc_paths"][tier] = add("reloc_" + tier, None, tier + "/output/hypoDD.reloc")
            elif tier in native:
                out["reloc_paths"][tier] = add("reloc_" + tier, native[tier])
            rows = csv_rows(base / out["catalogs"][tier])
            counts[tier] = len(rows)
            union.update(r["event_id"] for r in rows)
        if not out["catalogs"]:
            raise ValueError("Relocation payload must provide explicit tier catalog paths")
        out["event_mapping_path"] = add("event_mapping", outputs.get("event_mapping_path", outputs.get("event_mapping")), "event_lineage.csv")
        out["residuals_before_after_paths"] = []
        for value in ("qc/tier_comparison.json", "qc/tier_comparison.png"):
            if (base / value).exists():
                out["residuals_before_after_paths"].append(add("comparison_" + Path(value).suffix, value))
        doc["outputs"] = out
        doc["solver"].pop("trial_curve_path", None)
        curves = doc["solver"].get("trial_curve_paths")
        if curves is None:
            curves = {tier: tier + "/qc/damping_trials.png" for tier in paths
                      if (base / tier / "qc/damping_trials.png").is_file()}
        if curves:
            doc["solver"]["trial_curve_paths"] = {tier: add("trial_" + tier, value) for tier, value in curves.items()}
        else:
            doc["solver"].pop("trial_curve_paths", None)
        vm = doc["solver"].get("velocity_model", {})
        if vm.get("file"):
            vm["p_path"] = add("vp_model", vm.pop("file"))
        doc["tiers"]["paths"] = dict(out["catalogs"])
        doc["stats"].update(events_relocated=len(union), tier_counts=counts)
    elif stage == "mechanism":
        raise ValueError("No legacy mechanism implementation is known; publish a native v2 contract")
    else:
        raise ValueError("Unsupported stage: " + stage)
    return doc


def migrate(source, stage, output=None):
    source = Path(source).resolve()
    output = Path(output).resolve() if output else source.parent / "contract.v2.json"
    if output == source:
        raise ValueError("Migration must preserve the source contract")
    if output.parent != source.parent:
        raise ValueError("Place the revision beside its source so relative product paths stay stable")
    if output.exists():
        raise ValueError("Revision already exists; use a new explicit output filename")
    before = sha256(source)
    doc = write_v2(normalize(source, stage), output)
    assert before == sha256(source)
    return {"stage": stage, "path": str(output), **doc["validation"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--stage", choices=list(NAMES), required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    print(json.dumps(migrate(args.source, args.stage, args.out), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
