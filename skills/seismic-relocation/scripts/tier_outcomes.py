"""Distinguish a verified empty computation from missing or failed execution."""
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_files(base, entries):
    for name, expected in entries.items():
        path = Path(base) / name
        if not path.is_file() or sha(path) != expected:
            raise ValueError("Tier evidence changed or is missing: " + str(path))


def pairing_result(directory):
    directory = Path(directory)
    path = directory / "qc/pairing_result.json"
    if not path.exists():
        return None
    doc = json.loads(path.read_text())
    check_files(directory, doc["inputs"])
    check_files(directory, doc["outputs"])
    if doc["status"] == "EMPTY":
        dt = directory / "input/dt.ct"
        if doc.get("exit") != 0 or not dt.is_file() or any(
                line.strip() and not line.startswith("#") for line in dt.read_text().splitlines()):
            raise ValueError("Empty pairing is not backed by a successful zero-observation run")
    return doc


def outcome(directory):
    directory = Path(directory)
    pair = pairing_result(directory)
    if pair is not None and pair["status"] == "EMPTY":
        return {"status": "EMPTY", "reason": "NO_DIFFERENTIAL_TIMES", "damp": None}
    final_path = directory / "qc/final_run.json"
    selection_path = directory / "qc/damping_selection.json"
    if not selection_path.exists():
        return {"status": "UNAVAILABLE", "reason": "DAMPING_EVIDENCE_MISSING", "damp": None}
    selection = json.loads(selection_path.read_text())
    context = selection.get("context", {})
    inputs = context.get("input_sha256", {})
    has_ct = {"dt.ct", "event.dat", "station.dat"}.issubset(inputs)
    has_cc = {"dt.cc", "event.dat", "station.dat"}.issubset(inputs)
    if not (has_ct or has_cc):
        return {"status": "UNAVAILABLE", "reason": "INPUT_EVIDENCE_MISSING", "damp": None}
    if has_ct and has_cc and context.get("data_mode") == "cc":
        # A CC-only context must not carry catalog-differential evidence.
        return {"status": "UNAVAILABLE", "reason": "INPUT_EVIDENCE_MISSING", "damp": None}
    check_files(directory / "input", context.get("input_sha256", {}))
    if final_path.exists():
        final = json.loads(final_path.read_text())
        if set(final.get("artifacts", {})) != {"initial", "relocated"}:
            return {"status": "UNAVAILABLE", "reason": "FINAL_ARTIFACT_EVIDENCE_MISSING", "damp": None}
        for name, record in final.get("artifacts", {}).items():
            path = directory / "output" / ("hypoDD.loc" if name == "initial" else "hypoDD.reloc")
            if not path.exists() or sha(path) != record["sha256"]:
                raise ValueError("Final tier artifact differs from its execution record")
        if (final.get("status") == "PASS" and final.get("exit") == 0 and selection.get("status") == "SELECTED"
                and final.get("damp") is not None and final.get("damp") == selection.get("selected_damp")):
            return {"status": "READY", "reason": "SUPPORTED_FINAL_RUN", "damp": final["damp"]}
        if final.get("status") == "EMPTY" and final.get("exit") == 0 and final.get("artifacts"):
            if (directory / "output/hypoDD.reloc").read_text().strip():
                raise ValueError("Claimed empty tier contains relocated events")
            return {"status": "EMPTY", "reason": "NO_RELOCATED_EVENTS", "damp": final.get("damp")}
        return {"status": "UNAVAILABLE", "reason": "FINAL_EXECUTION_FAILED_OR_UNSUPPORTED", "damp": None}
    trials = selection.get("per_trial", [])
    if trials and all(r.get("status") == "EMPTY" and r.get("exit") == 0 for r in trials):
        for trial in trials:
            if set(trial.get("artifacts", {})) != {"initial", "relocated"}:
                raise ValueError("Empty trial is missing native execution evidence")
            for artifact in trial["artifacts"].values():
                if sha(artifact["path"]) != artifact["sha256"]:
                    raise ValueError("Empty trial artifact changed")
            record = trial["artifacts"]["relocated"]
            path = Path(record["path"])
            if sha(path) != record["sha256"] or path.read_text().strip():
                raise ValueError("Empty trial evidence is inconsistent")
        return {"status": "EMPTY", "reason": "NO_RELOCATED_EVENTS_IN_TRIALS", "damp": None}
    return {"status": "UNAVAILABLE", "reason": "NO_SUPPORTED_FINAL_RUN", "damp": None}
