"""Spatial evidence for the project's HypoDD damping rule; distances are km.

Horizontal coordinates use a shared WGS84 surface tangent plane per comparison.
The third coordinate is the reported depth, positive down, so Earth curvature
does not masquerade as a change in focal depth. Comparisons are by event ID and
initial cluster, on the same retained events in both catalogs.
"""
from pathlib import Path

import numpy as np

RULE_VERSION = "spatial-evidence-1.7"


def load_catalog(path):
    """Read native .loc (18 fields) or .reloc (24 fields), rejecting bad IDs."""
    records = {}
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith(("*", "#")):
            continue
        fields = line.split()
        if len(fields) not in (18, 24):
            raise ValueError(f"{path}:{number}: expected native loc/reloc row")
        event_id, cluster = int(fields[0]), int(fields[-1])
        lat, lon, depth = map(float, fields[1:4])
        if event_id in records:
            raise ValueError(f"{path}:{number}: duplicate event ID {event_id}")
        if not np.isfinite([lat, lon, depth]).all() or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"{path}:{number}: invalid coordinates")
        records[event_id] = (lat, lon, depth, cluster)
    return records


def project_km(positions, origin):
    """WGS84 surface E/N in km at (lat, lon); reported depth remains in km."""
    positions = np.asarray(positions, dtype=float)
    lat, lon = np.deg2rad(positions[:, :2]).T
    lat0, lon0 = np.deg2rad(origin)
    a, e2 = 6378.137, 6.6943799901413165e-3
    radius = a / np.sqrt(1 - e2 * np.sin(lat) ** 2)
    xyz = np.column_stack((radius * np.cos(lat) * np.cos(lon),
                           radius * np.cos(lat) * np.sin(lon),
                           radius * (1 - e2) * np.sin(lat)))
    radius0 = a / np.sqrt(1 - e2 * np.sin(lat0) ** 2)
    center = radius0 * np.array([np.cos(lat0) * np.cos(lon0),
                                 np.cos(lat0) * np.sin(lon0),
                                 (1 - e2) * np.sin(lat0)])
    east = np.array([-np.sin(lon0), np.cos(lon0), 0.0])
    north = np.array([-np.sin(lat0) * np.cos(lon0),
                      -np.sin(lat0) * np.sin(lon0), np.cos(lat0)])
    delta = xyz - center
    return np.column_stack((delta @ east, delta @ north, positions[:, 2]))


def aligned_clusters(first, second):
    common = sorted(first.keys() & second.keys())
    if any(first[k][3] != second[k][3] for k in common):
        raise ValueError("Cluster membership changed: compare trials with the same pairing/configuration")
    for cluster in sorted({first[k][3] for k in common}):
        ids = [k for k in common if first[k][3] == cluster]
        a = np.array([first[k][:3] for k in ids])
        b = np.array([second[k][:3] for k in ids])
        # Circular longitude mean also handles regional catalogs across 180 degrees.
        lons = np.deg2rad(a[:, 1])
        origin = (float(a[:, 0].mean()),
                  float(np.rad2deg(np.arctan2(np.sin(lons).mean(), np.cos(lons).mean()))))
        yield cluster, ids, project_km(a, origin), project_km(b, origin)


def displacement_metrics(initial, relocated):
    clusters, event_shifts = [], []
    if relocated.keys() - initial.keys():
        raise ValueError("Relocated events absent from initial catalog")
    for cluster, ids, before, after in aligned_clusters(initial, relocated):
        delta = after - before
        centroid = delta.mean(axis=0)
        event_shifts.extend(np.linalg.norm(delta, axis=1).tolist())
        clusters.append({
            "cluster_id": cluster, "n_common": len(ids),
            "centroid_east_km": float(centroid[0]),
            "centroid_north_km": float(centroid[1]),
            "centroid_depth_change_km": float(centroid[2]),
            "centroid_horizontal_km": float(np.linalg.norm(centroid[:2])),
            "centroid_vertical_km": float(abs(centroid[2])),
            "centroid_shift_km": float(np.linalg.norm(centroid)),
        })
    return {
        "n_common": len(event_shifts), "n_not_retained": len(initial) - len(relocated),
        "event_displacement_median_km": float(np.median(event_shifts)) if event_shifts else None,
        "centroid_shift_km": max((c["centroid_shift_km"] for c in clusters), default=None),
        "centroid_horizontal_km": max((c["centroid_horizontal_km"] for c in clusters), default=None),
        "centroid_vertical_km": max((c["centroid_vertical_km"] for c in clusters), default=None),
        "clusters": clusters,
    }


def structure_metrics(first, second):
    """Remove each cluster's translation, preserving E/N/depth deformation."""
    clusters = []
    for cluster, ids, a, b in aligned_clusters(first, second):
        difference = None
        if len(ids) >= 2:
            delta = (b - b.mean(axis=0)) - (a - a.mean(axis=0))
            difference = float(np.median(np.linalg.norm(delta, axis=1)))
        clusters.append({"cluster_id": cluster, "n_common": len(ids),
                         "struct_diff_km": difference})
    # Missing/singleton clusters cannot silently qualify as a stable structure.
    expected = {r[3] for r in first.values()} | {r[3] for r in second.values()}
    evaluated = bool(clusters) and {c["cluster_id"] for c in clusters} == expected
    evaluated = evaluated and all(c["struct_diff_km"] is not None for c in clusters)
    return {
        "status": "EVALUATED" if evaluated else "NOT_EVALUATED",
        "n_common": sum(c["n_common"] for c in clusters),
        "common_fraction_first": sum(c["n_common"] for c in clusters) / len(first) if first else 0.0,
        "common_fraction_second": sum(c["n_common"] for c in clusters) / len(second) if second else 0.0,
        "struct_diff_km": max(c["struct_diff_km"] for c in clusters) if evaluated else None,
        "clusters": clusters,
    }


def select_damping(results, catalogs, initial_erh_km):
    """Smallest candidate supported by its next larger successful trial.

ERH is an explicit project comparison scale, not a 3-D confidence bound.
CND does not enter this selector. Failed or unassessed evidence cannot pass.
"""
    if not np.isfinite(initial_erh_km) or initial_erh_km <= 0:
        raise ValueError("initial ERH must be finite and positive")
    results = sorted((dict(r) for r in results), key=lambda r: r["damp"])
    if any(not np.isfinite(r["damp"]) or r["damp"] <= 0 for r in results):
        raise ValueError("DAMP must be finite and positive")
    if len({r["damp"] for r in results}) != len(results):
        raise ValueError("Duplicate damping candidates")
    for i, result in enumerate(results):
        result.update({"structure": {"status": "NOT_EVALUATED"},
                       "eligible": False, "reason": "no_larger_neighbor"})
        if result.get("status") != "PASS":
            result["reason"] = "trial_failed"
            continue
        if i + 1 == len(results):
            continue
        neighbor = results[i + 1]
        result["comparison_damp"] = neighbor["damp"]
        if neighbor.get("status") != "PASS":
            result["reason"] = "neighbor_failed"
            continue
        if result["damp"] not in catalogs or neighbor["damp"] not in catalogs:
            result["reason"] = "catalog_missing"
            continue
        comparison = structure_metrics(catalogs[result["damp"]], catalogs[neighbor["damp"]])
        result["structure"] = comparison
        shifts = [r.get("centroid_shift_km") for r in (result, neighbor)]
        if comparison["status"] != "EVALUATED":
            result["reason"] = "insufficient_common_events"
        elif any(s is None or not np.isfinite(s) for s in shifts):
            result["reason"] = "centroid_not_evaluated"
        elif max(shifts) >= initial_erh_km:
            result["reason"] = "centroid_above_comparison_scale"
        elif comparison["struct_diff_km"] >= initial_erh_km:
            result["reason"] = "structure_above_comparison_scale"
        else:
            result.update(eligible=True, reason="supported_by_adjacent_trial")
    plateau = [r["damp"] for r in results if r["eligible"]]
    return {
        "rule_version": RULE_VERSION,
        "rule": "project rule: adjacent centered structures and per-cluster centroid shifts below "
                "the supplied ERH comparison scale; choose smallest supported DAMP; CND is diagnostic",
        "initial_erh_km": initial_erh_km, "per_trial": results, "plateau": plateau,
        "selected_damp": min(plateau) if plateau else None,
        "status": "SELECTED" if plateau else "NEEDS_REVIEW",
        "note": "Shared-event structural stability does not validate lost events or absolute depths.",
    }
