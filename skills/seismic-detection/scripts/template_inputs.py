"""Content identity of waveforms used to cut templates, separate from scan-only days."""
import hashlib
import json
import shutil
from pathlib import Path

from contract_io import sha256


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def snapshot(adapter, runtime):
    adapter = Path(adapter)
    view = json.loads((adapter / "continuous_manifest.json").read_text())
    if "template_dates" not in view:
        raise ValueError("Template-date provenance is missing; regenerate the adapter")
    files = {}
    for item in view["files"]:
        if item["date"] not in view["template_dates"]:
            continue
        source, link = Path(item["source"]), Path(item["view"])
        if not source.is_file() or not link.is_symlink() or link.resolve() != source.resolve():
            raise ValueError("A template source or its declared link changed")
        files[str(source.resolve())] = sha256(source)
    if not files:
        raise ValueError("No waveforms cover the template dates")
    return {"version": 1, "waveforms": files,
            "phase_sha256": sha256(adapter / "templates.temp"),
            "view_sha256": sha256(adapter / "continuous_manifest.json"),
            "runtime_sha256": sha256(runtime)}


def verify_snapshot(adapter, runtime, store):
    path = Path(store) / "source_snapshot.json"
    if not path.is_file():
        raise ValueError("Template source snapshot missing; cut templates with the current runner")
    saved = json.loads(path.read_text())
    current = snapshot(adapter, runtime)
    if saved != current:
        raise ValueError("Template source waveforms/configuration changed; cached templates are invalid")
    return identity(current)


def prepare_cache(output, source):
    """Reuse only a validated build; discard uncommitted native partial caches."""
    output = Path(output)
    digest = identity(source)
    active = output / "active_template_source.json"
    scans = list((output / "steps").glob("scan_*.json"))
    if scans and (not active.is_file() or json.loads(active.read_text()).get("identity") != digest):
        raise ValueError("Template inputs changed after scanning; use a new output directory")
    store = output / "templates_medium" / digest
    marker = output / "steps" / ("cut_" + digest + ".json")
    if not marker.is_file():
        if store.exists():
            record = store / "source_snapshot.json"
            if store.is_symlink() or not record.is_file() or identity(json.loads(record.read_text())) != digest:
                raise ValueError("Unowned template cache directory")
            shutil.rmtree(store)
        store.mkdir(parents=True)
        (store / "source_snapshot.json").write_text(json.dumps(source, sort_keys=True, indent=2) + "\n")
    active.write_text(json.dumps({"identity": digest}, sort_keys=True) + "\n")
    return store
