"""Versioned contract publication, validation and consumption (no scientific computation).

Paths are relative to the contract file. The scientific environment needs only
the standard library; full JSON Schema validation may use the user-selected
existing interpreter in validator_config.json.
"""
import argparse
import copy
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VERSION = "2.0"
NAMES = {"preprocess": "downstream_contract.json", "picking": "picking.contract.json",
         "association": "association.contract.json", "location": "location_contract.json",
         "relocation": "relocation_contract.json", "detection": "detection_contract.json",
         "post_detection_relocation": "post_detection_relocation_contract.json",
         "mechanism": "mechanism_contract.json"}


def supported_version(doc):
    expected = "2.1" if doc.get("stage") == "detection" else VERSION
    return doc.get("contract_version") == expected


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def relative(path, base):
    return os.path.relpath(Path(path).resolve(), Path(base).resolve())


def schema_errors(doc):
    try:
        import jsonschema
        validator_type = jsonschema.Draft202012Validator
    except (ImportError, AttributeError):
        from runtime_support import runtime_path
        python = os.environ.get("SEISFLOW_VALIDATOR_PYTHON") or runtime_path("validator_python")
        if not python:
            raise RuntimeError("Full JSON Schema validation requires jsonschema or an explicit validator_python in runtime.local.json")
        python = str(python)
        if Path(python).resolve() == Path(sys.executable).resolve():
            raise RuntimeError("Configured validator lacks jsonschema Draft202012Validator")
        result = subprocess.run([python, "-B", str(__file__), "schema-stdin"],
                                input=json.dumps(doc), text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError("Schema validator failed: " + result.stderr)
        return json.loads(result.stdout)
    stage = doc.get("stage")
    if stage not in NAMES:
        return ["Unknown stage"]
    schemas = {p.name: json.loads(p.read_text()) for p in HERE.glob("*.schema.json")}
    schema = schemas[stage + ".contract.schema.json"]
    for item in schemas.values():
        validator_type.check_schema(item)
    resolver = jsonschema.RefResolver(base_uri=HERE.as_uri() + "/", referrer=schema,
                                      store=schemas)
    checker = jsonschema.FormatChecker()
    # jsonschema's optional RFC3339 dependency is not present in every existing
    # environment. Validate our generated ISO timestamps explicitly, without installs.
    @checker.checks("date-time", raises=(ValueError, TypeError))
    def timestamp_with_zone(value):
        if not isinstance(value, str):
            return True  # the schema's type validator handles other types
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})", value):
            return False
        parsed = datetime.fromisoformat(value.replace("t", "T").replace("z", "+00:00").replace("Z", "+00:00"))
        return parsed.utcoffset() is not None
    validator = validator_type(schema, resolver=resolver, format_checker=checker)
    return ["/" + "/".join(map(str, e.absolute_path)) + ": " + e.message
            for e in sorted(validator.iter_errors(doc), key=lambda e: str(list(e.absolute_path)))]


def csv_rows(path):
    path = Path(path)
    files = sorted(path.rglob("*.csv")) if path.is_dir() else [path]
    result = []
    for file in files:
        with file.open(newline="") as stream:
            result.extend(csv.DictReader(stream))
    return result


def columns(path):
    path = Path(path)
    if path.is_dir():
        path = next(iter(sorted(path.rglob("*.csv"))))
    with path.open(newline="") as stream:
        return next(csv.reader(stream))


def lookup(doc, key):
    for part in key.split("."):
        doc = doc[part]
    return doc


def path_fields(doc):
    """Only operational fields; prose, warnings and source history are not paths."""
    for key in ("qc_path", "config_path", "script_path", "manifest_path", "archive_root"):
        if doc.get(key):
            yield key, doc[key]
    for i, item in enumerate(doc.get("upstream", [])):
        yield "upstream." + str(i), item["contract_path"]
    stage = doc["stage"]
    fields = {
        "preprocess": [], "picking": ["outputs.picks_path"],
        "association": ["outputs.events_path", "outputs.assignments_path", "stats.unassociated_picks_path",
                        "station_source.path", "velocity_model.path", "velocity_model.p_path", "velocity_model.s_path",
                        "params.rationale_path"],
        "location": ["outputs.catalog_path", "outputs.arc_path", "outputs.prt_path", "outputs.sum_path",
                     "outputs.rejected_path", "model_file.p_path", "model_file.s_path",
                     "station_file.path", "station_file.generated_from", "phase_file.path"],
        "relocation": ["outputs.event_mapping_path", "solver.velocity_model.p_path"],
        "detection": ["outputs.detections_path", "outputs.new_events_path", "template_source.contract_path",
                      "template_source.catalog_path", "outputs.phase_path", "outputs.event_path",
                      "outputs.dt_cc_path", "outputs.reference_events_path"],
        "mechanism": ["outputs.mechanisms_path"],
        "post_detection_relocation": ["solver.parameters_path"],
    }[stage]
    for key in fields:
        try:
            value = lookup(doc, key)
        except KeyError:
            continue
        yield key, value
    for key in ("outputs.catalogs", "outputs.reloc_paths", "solver.trial_curve_paths", "outputs.event_mapping_paths"):
        try:
            values = lookup(doc, key)
        except KeyError:
            continue
        for name, value in values.items():
            yield key + "." + name, value
    for name, values in doc.get("outputs", {}).get("per_tier", {}).items():
        for field, value in values.items():
            yield "outputs.per_tier." + name + "." + field, value
    for i, check in enumerate(doc.get("verification", [])):
        for j, value in enumerate(check["evidence_paths"]):
            yield "verification.%s.%s" % (i, j), value


def inspect_artifacts(doc, base):
    base = Path(base)
    issues = []
    def issue(code, message, artifact=""):
        issues.append({"code": code, "message": message, "artifact": artifact})
    registered = {a["path"] for a in doc["artifacts"].values()}
    if doc.get("status") == "READY" and doc.get("qc_path"):
        qc = base / doc["qc_path"]
        if qc.is_dir() and not any(p.is_file() for p in qc.rglob("*")):
            issue("EMPTY_QC", "READY requires an actual QC artifact, not an empty directory")
    for field, value in path_fields(doc):
        if value not in registered:
            issue("UNREGISTERED_PATH", field + " does not reference a declared artifact", field)
    for name, artifact in doc["artifacts"].items():
        path = base / artifact["path"]
        if not path.exists():
            if artifact["required"]:
                issue("MISSING_ARTIFACT", str(path), name)
            continue
        if (artifact["kind"] == "file") != path.is_file():
            issue("ARTIFACT_KIND", str(path), name)
        elif path.is_file() and artifact.get("sha256") != sha256(path):
            issue("ARTIFACT_HASH", str(path), name)
    for item in doc.get("upstream", []):
        path = base / item["contract_path"]
        if path.is_file():
            upstream = json.loads(path.read_text())
            if upstream.get("stage") != item["stage"] or not supported_version(upstream):
                issue("UPSTREAM_IDENTITY", str(path))
    stage = doc["stage"]
    def read(key):
        path = base / lookup(doc, key)
        return csv_rows(path) if path.exists() else None
    def compare(actual, expected, description):
        if expected is not None and actual != expected:
            issue("COUNT_MISMATCH", "%s: %s != %s" % (description, actual, expected))
    def unique(rows, description):
        ids = [r.get("event_id", "") for r in rows]
        if any(not i for i in ids):
            issue("MISSING_EVENT_ID", description)
        if len(ids) != len(set(ids)):
            issue("DUPLICATE_EVENT_ID", "%s: %d rows, %d unique IDs" % (description, len(ids), len(set(ids))), description)
        return set(ids)
    def upstream_ids(wanted, field):
        for item in doc.get("upstream", []):
            if item["stage"] == wanted:
                parent_path = base / item["contract_path"]
                if parent_path.is_file():
                    parent = json.loads(parent_path.read_text())
                    catalog = parent_path.parent / lookup(parent, field)
                    if catalog.is_file():
                        return {r["event_id"] for r in csv_rows(catalog)}
        return None
    if stage == "preprocess":
        rows = read("manifest_path")
        if rows is not None:
            compare(len(rows), doc["stats"]["group_days"], "group-days")
        band = doc["data_contract"]["target_band_hz"]
        if not (band[0] < band[1] < doc["data_contract"]["sampling_rate_hz"] / 2):
            issue("INVALID_BAND", "Band must increase and stay below Nyquist")
    elif stage == "picking":
        rows = read("outputs.picks_path")
        if rows is not None:
            for kind in ("p", "s"):
                compare(sum(r["phase_type"].lower() == kind for r in rows),
                        doc.get("stats", {}).get("n_" + kind), "picks " + kind)
    elif stage == "association":
        events, picks, unused = read("outputs.events_path"), read("outputs.assignments_path"), read("stats.unassociated_picks_path")
        if events is not None and picks is not None and unused is not None:
            unique(events, "events")
            known = {int(r["event_index"]) for r in events}
            assigned = [r for r in picks if int(r["event_index"]) >= 0]
            if any(int(r["event_index"]) not in known for r in assigned):
                issue("BROKEN_EVENT_REFERENCE", "Assignments refer to absent events")
            compare(len(events), doc["stats"]["n_events"], "events")
            compare(len(assigned), doc["stats"]["picks_associated"], "associated picks")
            compare(len(assigned) + len(unused), doc["stats"]["picks_in"], "all picks")
    elif stage == "location":
        rows, rejected = read("outputs.catalog_path"), read("outputs.rejected_path")
        if rows is not None and rejected is not None:
            located_ids = unique(rows, "located events")
            rejected_ids = unique(rejected, "rejected events")
            compare(len(rows), doc["stats"]["located"], "located")
            compare(len(rejected), doc["stats"]["rejected"], "rejected")
            compare(len(rows) + len(rejected), doc["stats"]["events_in"], "input events")
            if located_ids & rejected_ids:
                issue("OVERLAPPING_OUTCOMES", "Located and rejected events overlap")
            expected = upstream_ids("association", "outputs.events_path")
            if expected is not None and (located_ids | rejected_ids) != expected:
                issue("BROKEN_EVENT_REFERENCE", "Located plus rejected IDs differ from the association catalog")
    elif stage == "relocation":
        union = set()
        statuses = doc.get("tiers", {}).get("statuses", {})
        for tier, state in statuses.items():
            present = tier in doc["outputs"]["catalogs"]
            if state["status"] == "UNAVAILABLE" and present:
                issue("TIER_OUTCOME", "Unavailable tier must not masquerade as an empty catalog", tier)
            if state["status"] in ("READY", "EMPTY") and not present:
                issue("TIER_OUTCOME", "Completed or empty tier needs a catalog", tier)
            if state["status"] == "READY" and tier not in doc["outputs"]["reloc_paths"]:
                issue("TIER_OUTCOME", "Ready tier needs its native relocation output", tier)
        if statuses and doc["status"] == "READY" and any(s["status"] != "READY" for s in statuses.values()):
            issue("TIER_OUTCOME", "An incomplete or empty tier requires overall PARTIAL status")
        for tier in doc["outputs"]["catalogs"]:
            rows = read("outputs.catalogs." + tier)
            if rows is not None:
                if statuses.get(tier, {}).get("status") == "EMPTY" and rows:
                    issue("TIER_OUTCOME", "Empty tier contains events", tier)
                if statuses.get(tier, {}).get("status") == "READY" and not rows:
                    issue("TIER_OUTCOME", "Ready tier contains no events", tier)
                union.update(unique(rows, "catalog_" + tier))
                compare(len(rows), doc["stats"].get("tier_counts", {}).get(tier), tier)
        compare(len(union), doc["stats"]["events_relocated"], "relocated union")
        expected = upstream_ids("location", "outputs.catalog_path")
        if expected is not None and not union.issubset(expected):
            issue("BROKEN_EVENT_REFERENCE", "Relocated IDs are absent from the upstream location catalog")
    elif stage == 'post_detection_relocation':
        union = set()
        for tier, state in doc['tiers'].items():
            present = tier in doc['outputs']['catalogs']
            if present != (state['status'] in ('READY', 'EMPTY')):
                issue('TIER_OUTCOME', 'Joint catalog presence disagrees with its outcome', tier)
            if doc['status'] == 'READY' and state['status'] != 'READY':
                issue('TIER_OUTCOME', 'Incomplete joint tier requires PARTIAL status', tier)
            if state['status'] == 'READY' and tier not in doc['outputs']['reloc_paths']:
                issue('TIER_OUTCOME', 'Ready joint tier lacks native solver output', tier)
            if not present:
                if doc['stats']['tier_counts'][tier] is not None:
                    issue('TIER_OUTCOME', 'Unavailable count must be null', tier)
                continue
            rows = read('outputs.catalogs.'+tier)
            if rows is not None:
                union.update(unique(rows, tier))
                compare(len(rows), doc['stats']['tier_counts'][tier], tier)
                if state['status'] == 'EMPTY' and rows:
                    issue('TIER_OUTCOME', 'Empty joint tier contains events', tier)
                if state['status'] == 'READY' and not rows:
                    issue('TIER_OUTCOME', 'Ready joint tier contains no detected events', tier)
                if any(r.get('location_method') != 'hypodd_cc_ct' or r.get('ct_source') != 'independent_phasenet'
                       or r.get('role') != 'detection' for r in rows):
                    issue('JOINT_PROVENANCE', 'Joint output contains unsupported locations or references', tier)
                parents = [base/u['contract_path'] for u in doc['upstream'] if u['stage'] == 'detection']
                matching = [p for p in parents if p.parent.name == tier]
                if len(matching) != 1:
                    issue('BROKEN_EVENT_REFERENCE', 'Missing unique CC-tier upstream', tier)
                else:
                    parent = json.loads(matching[0].read_text())
                    expected = {r['event_id'] for r in csv_rows(matching[0].parent/parent['outputs']['detections_path'])}
                    if not {r['event_id'] for r in rows}.issubset(expected):
                        issue('BROKEN_EVENT_REFERENCE', 'Relocated detection absent from its MESS tier', tier)
        compare(len(union), doc['stats']['unique_relocated_detection_events'], 'joint relocated union')
    elif stage == "detection":
        for key, count in (("detections_path", "after_dedup"), ("new_events_path", "new_events")):
            rows = read("outputs." + key)
            if rows is not None:
                unique(rows, key)
                compare(len(rows), doc["stats"].get(count), key)
                if any(float(r["best_detection_cc"]) < doc["selection"]["cc_min"] for r in rows):
                    issue("BELOW_CATALOG_THRESHOLD", key)
        rows = read("outputs.detections_path")
        if rows is not None:
            ids = {int(r["event_id"]) for r in rows}
            unused = read("outputs.new_events_path")
            if unused is not None and not {int(r["event_id"]) for r in unused}.issubset(ids):
                issue("BROKEN_EVENT_REFERENCE", "New candidates are absent from this CC catalog")
            paths = {k: base / doc["outputs"][k] for k in
                     ("phase_path", "event_path", "dt_cc_path", "reference_events_path")}
            if all(p.is_file() for p in paths.values()):
                phase_ids = []
                for line in paths["phase_path"].read_text().splitlines():
                    fields = next(csv.reader([line])) if line.strip() else []
                    if fields and re.match(r"^\d{4}-\d{2}-\d{2}", fields[0]):
                        phase_ids.append(int(fields[5]))
                native = [int(line.split()[-1]) for line in paths["event_path"].read_text().splitlines() if line.strip()]
                references = set(json.loads(paths["reference_events_path"].read_text())["event_ids"])
                if set(phase_ids) != ids or len(phase_ids) != len(ids):
                    issue("BROKEN_EVENT_REFERENCE", "Phase events differ from this CC catalog")
                if set(native) != ids | references or len(native) != len(set(native)):
                    issue("BROKEN_EVENT_REFERENCE", "Native events differ from detections plus declared template references")
                for line in paths["dt_cc_path"].read_text().splitlines():
                    if line.startswith("#"):
                        a, b = map(int, line.split()[1:3])
                        if a not in native or b not in native:
                            issue("BROKEN_EVENT_REFERENCE", "Differential time refers to an absent native event")
    return issues


def contract_file(path, stage):
    path = Path(path).resolve()
    if path.is_dir():
        current = path / "contract.v2.json"
        if current.is_file():
            return current
        path = path / NAMES[stage]
    if not path.is_file():
        raise ValueError("Contract missing: " + str(path))
    doc = json.loads(path.read_text())
    if supported_version(doc):
        return path
    current = path.parent / "contract.v2.json"
    if current.is_file():
        revision = json.loads(current.read_text())
        provenance = revision.get("provenance", {})
        if provenance.get("source_contract_sha256") == sha256(path):
            return current
    raise ValueError("Legacy or stale contract requires explicit migration: " + str(path))


def load_contract(path, stage, check_artifacts=True, _seen=None):
    path = contract_file(path, stage)
    seen = set() if _seen is None else set(_seen)
    if path in seen:
        raise ValueError("Contract dependency cycle: " + str(path))
    seen.add(path)
    doc = json.loads(path.read_text())
    errors = schema_errors(doc)
    if doc.get("stage") != stage or errors:
        raise ValueError("Contract schema/identity failure: " + "; ".join(errors))
    if doc["status"] == "FAILED":
        raise ValueError("Upstream stage failed: " + str(path))
    if check_artifacts:
        issues = inspect_artifacts(doc, path.parent)
        if issues:
            raise ValueError("Contract artifact failure: " + json.dumps(issues[:5], ensure_ascii=False))
        for upstream in doc["upstream"]:
            load_contract(path.parent / upstream["contract_path"], upstream["stage"], True, seen)
    return doc, path


def product_path(path, stage, field):
    doc, source = load_contract(path, stage)
    return (source.parent / lookup(doc, field)).resolve()


def archive_fingerprint(doc):
    dc = doc["data_contract"]
    return {"sampling_rate_hz": dc["sampling_rate_hz"], "band_hz": dc["target_band_hz"],
            "units": dc["units"], "physical_quantity": dc["physical_quantity"],
            "response_removed": dc["response_removed"], "components": dc["archive_component_labels"]}


def write_v2(doc, output):
    output = Path(output).resolve()
    errors = schema_errors(doc)
    if errors:
        raise ValueError("Cannot publish malformed contract: " + "; ".join(errors))
    issues = inspect_artifacts(doc, output.parent)
    doc["validation"] = {"schema_status": "PASS", "artifact_status": "FAIL" if issues else "PASS",
                         "scientific_status": "NOT_TESTED", "issues": issues}
    if issues and doc["status"] == "READY":
        doc["status"] = "PARTIAL"
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(output)
    return doc


def publish_payload(payload, output, stage):
    """Capture a producer payload and publish its validated v2 representation."""
    from migrate_contracts import normalize
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Preserve existing contracts; choose a new revision path: " + str(output))
    source = output.with_name(output.stem + ".source.json")
    if source.exists():
        raise ValueError("Source payload snapshot already exists: " + str(source))
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    doc = normalize(source, stage)
    if supported_version(payload):
        previous = copy.deepcopy(doc.get("provenance", {}))
        doc["provenance"] = {"source_contract_path": source.name,
            "source_contract_sha256": sha256(source), "source_contract_version": payload["contract_version"],
            "revision_created_at": now(), "source_created_at": payload.get("created_at"),
            "notes": ["Native v2 payload publication; prior provenance is retained in the source snapshot."],
            "prior_provenance": previous}
        doc["artifacts"]["source_contract"] = {"path": source.name, "kind": "file",
                                              "required": True, "sha256": sha256(source)}
    result = write_v2(doc, output)
    if output.name != "contract.v2.json" and not output.with_name("contract.v2.json").exists():
        write_v2(copy.deepcopy(result), output.with_name("contract.v2.json"))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["schema-stdin", "validate", "publish"])
    ap.add_argument("path", nargs="?")
    ap.add_argument("--stage", choices=list(NAMES))
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.command == "schema-stdin":
        print(json.dumps(schema_errors(json.load(sys.stdin))))
        return
    if args.command == "publish":
        doc = publish_payload(json.loads(Path(args.path).read_text()), args.out, args.stage)
    else:
        path = Path(args.path).resolve()
        doc = json.loads(path.read_text())
        errors = schema_errors(doc)
        issues = inspect_artifacts(doc, path.parent) if not errors else []
        print(json.dumps({"schema_errors": errors, "artifact_issues": issues}, indent=2, ensure_ascii=False))
        sys.exit(1 if errors or issues else 0)
    print(json.dumps(doc["validation"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
