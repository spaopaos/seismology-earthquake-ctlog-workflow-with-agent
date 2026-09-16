"""Require a single relocation -> location -> association -> picking -> archive lineage."""
from pathlib import Path
import csv

from contract_io import load_contract, sha256


def parent(child, stage):
    doc, path = child
    matches = [item for item in doc["upstream"] if item["stage"] == stage]
    if len(matches) != 1:
        raise ValueError(f"LINEAGE: {path} must name exactly one {stage} parent")
    return load_contract(path.parent / matches[0]["contract_path"], stage)


def same(left, right, stage):
    if left[1].resolve() != right[1].resolve() or sha256(left[1]) != sha256(right[1]):
        raise ValueError(f"LINEAGE: supplied {stage} belongs to a different run: {left[1]} != {right[1]}")


def load_mess_contracts(archive, relocation, association=None, location=None):
    relocation = load_contract(relocation, "relocation")
    inherited_location = parent(relocation, "location")
    if location is not None:
        same(load_contract(location, "location"), inherited_location, "location")
    inherited_association = parent(inherited_location, "association")
    if association is not None:
        same(load_contract(association, "association"), inherited_association, "association")
    picking = parent(inherited_association, "picking")
    inherited_archive = parent(picking, "preprocess")
    same(load_contract(archive, "preprocess"), inherited_archive, "preprocess")
    doc, path = relocation
    state = doc.get("tiers", {}).get("statuses", {}).get("medium", {}).get("status")
    if state is not None and state != "READY":
        raise ValueError(f"MEDIUM_UNAVAILABLE: medium tier is {state}; another tier cannot replace it")
    medium = doc["outputs"]["catalogs"].get("medium")
    if medium is None:
        raise ValueError("MEDIUM_UNAVAILABLE: no medium catalog")
    with (path.parent / medium).open() as stream:
        if next(csv.DictReader(stream), None) is None:
            raise ValueError("MEDIUM_UNAVAILABLE: medium catalog is empty")
    return {"preprocess": inherited_archive, "relocation": relocation,
            "association": inherited_association, "location": inherited_location}
