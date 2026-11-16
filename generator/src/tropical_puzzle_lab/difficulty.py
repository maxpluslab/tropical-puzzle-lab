"""Computed difficulty rating: how much a computer search has to try to assemble the puzzle.

The rating comes from the exhaustive contact search of the sibling repository tiling-solvers
(`rust.contact_dfs`), run on each variant in its own regime: a relief variant with its roofs,
which must agree along shared edges, and a flat variant as footprints only. The search gets
a sanitized instance (pieces turned, shuffled and renamed, no reference). Its counts are
committed in puzzles/solver-metrics.json by generator/scripts/solver_metrics.py, because the
search is not a dependency of the generator.

1. nodes = placements the search tries to find every assembly and show there is no other.
   A search stopped at the node limit gives a lower bound.
2. x = log10(nodes), mapped to a 1-5 rating by RATING_THRESHOLDS below (5 = hardest).

This is search effort, not measured human difficulty. Roofs give the matching away, so most
relief variants rate 1.

A secondary statistic is published next to the rating without driving it: the
Leinster-Cobbold diversity of the pieces' intrinsic volumes, each piece taken as the convex
solid the player draws (footprint extruded from z = 0 to its roof plane or thickness).

1. Intrinsic volumes of each convex piece P (from the convex hull of its vertices):
       V0 = 1
       V1 = (1 / 2pi) * sum over edges of  length * (pi - interior dihedral angle)
       V2 = surface area / 2
       V3 = volume
2. Scale-free shape vector, with L = (sum of all piece volumes)^(1/3):
       d(P) = (V0, V1 / L, sqrt(V2) / L, cbrt(V3) / L)
3. Distances d_ij = |d(P_i) - d(P_j)| (Euclidean), similarities Z_ij = exp(-u * d_ij).
4. Leinster-Cobbold diversity of order q = DIVERSITY_ORDER (default 2) with uniform weights 1/n:
       D = n^2 / sum_ij Z_ij,  1 <= D <= n  (the effective number of distinct pieces).

The parameters below are the only definition of the method's constants. `tpl-export`
copies them into puzzles/index.json, and the explanation page reads them from there.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

# ---------------------------------------------------------------------------
# CONFIGURATION: tune the rating here and rerun `tpl-export`.
# ---------------------------------------------------------------------------

#: Four increasing cut points on x = log10(nodes of the whole search). k = number of cut
#: points <= x (0..4); the rating is 1 + k. Calibrated (2026-11) on the gallery: one shared
#: scale for relief and flat variants, so a rating means the same search effort on both.
#: Nodes run from 26 (Hill 6a-r, Bowl 9a-r) to over 1.5 million (Corrugated 27a-f, unfinished).
RATING_THRESHOLDS = (2.0, 3.0, 4.0, 5.5)

#: Secondary statistic only. Similarity sharpness u in Z_ij = exp(-u * d_ij).
SIMILARITY_U = 10.0

#: Secondary statistic only. Order q of the Leinster-Cobbold diversity (q >= 0; math.inf allowed).
#: q = 2 gives D = n^2 / sum_ij Z_ij.
DIVERSITY_ORDER = 2.0

#: Where solver_metrics.py writes the search counts, relative to the puzzles directory.
METRICS_FILE = "solver-metrics.json"

# ---------------------------------------------------------------------------

#: Points closer than this (relative to the piece size) are the same point, and points this
#: close to a supporting plane lie on that face, so near-coplanar facets merge into one face.
FLAT_TOLERANCE = 1e-9

Vec3 = tuple[float, float, float]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    return math.sqrt(_dot(a, a))


@dataclass(frozen=True)
class Face:
    normal: Vec3  # outward unit normal
    offset: float  # normal . p for points p on the face
    vertices: tuple[int, ...]  # indices into the hull points, counter-clockwise seen from outside
    area: float


def _hull2d(points: list[tuple[float, float, int]], eps: float) -> list[int]:
    """Counter-clockwise convex hull (Andrew's monotone chain) without collinear points."""
    pts = sorted(points)
    if len(pts) < 3:
        return [p[2] for p in pts]

    def turn(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def chain(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and turn(out[-2], out[-1], p) <= eps * max(1.0, math.dist(out[-2][:2], p[:2])):
                out.pop()
            out.append(p)
        return out

    lower, upper = chain(pts), chain(reversed(pts))
    return [p[2] for p in lower[:-1] + upper[:-1]]


def convex_hull(vertices: Sequence[Sequence[float]]) -> tuple[list[Vec3], list[Face]]:
    """Faces of the convex hull of a small 3D point set, with coplanar facets merged.

    Brute force over point triples (pieces have at most a few dozen vertices): a triple spans a
    face plane when every point lies on one side of it within the tolerance.
    """
    raw = [tuple(float(c) for c in v) for v in vertices]
    size = max(max(abs(c) for c in v) for v in raw) or 1.0
    span = max(math.dist(a, b) for a in raw for b in raw)
    eps = FLAT_TOLERANCE * max(size, span)
    points: list[Vec3] = []
    for v in raw:
        if all(math.dist(v, p) > eps for p in points):
            points.append(v)
    if len(points) < 4:
        raise ValueError("convex hull is degenerate (fewer than four distinct points)")

    planes: list[tuple[Vec3, float]] = []
    n = len(points)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                normal = _cross(_sub(points[j], points[i]), _sub(points[k], points[i]))
                length = _norm(normal)
                if length <= eps * span:
                    continue
                normal = (normal[0] / length, normal[1] / length, normal[2] / length)
                offset = _dot(normal, points[i])
                sides = [_dot(normal, p) - offset for p in points]
                if all(s <= eps for s in sides):
                    plane = (normal, offset)
                elif all(s >= -eps for s in sides):
                    plane = ((-normal[0], -normal[1], -normal[2]), -offset)
                else:
                    continue
                if not any(_dot(plane[0], q[0]) > 1 - FLAT_TOLERANCE and abs(plane[1] - q[1]) <= eps for q in planes):
                    planes.append(plane)
    if len(planes) < 4:
        raise ValueError("convex hull is degenerate (flat point set)")

    faces = []
    for normal, offset in planes:
        on = [i for i, p in enumerate(points) if abs(_dot(normal, p) - offset) <= eps]
        # Right-handed basis (e1, e2, normal) of the face plane.
        helper = (1.0, 0.0, 0.0) if abs(normal[0]) < 0.9 else (0.0, 1.0, 0.0)
        e1 = _cross(helper, normal)
        e1 = tuple(c / _norm(e1) for c in e1)
        e2 = _cross(normal, e1)
        ring = _hull2d([(_dot(points[i], e1), _dot(points[i], e2), i) for i in on], eps)
        coords = [(_dot(points[i], e1), _dot(points[i], e2)) for i in ring]
        area = 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(coords, coords[1:] + coords[:1]))
        faces.append(Face(normal, offset, tuple(ring), area))
    return points, faces


@dataclass(frozen=True)
class IntrinsicVolumes:
    v0: float
    v1: float
    v2: float
    v3: float


def intrinsic_volumes(vertices: Sequence[Sequence[float]]) -> IntrinsicVolumes:
    """V0..V3 of the convex hull of `vertices`."""
    points, faces = convex_hull(vertices)
    edges: dict[tuple[int, int], list[Vec3]] = {}
    for face in faces:
        ring = face.vertices
        for a, b in zip(ring, ring[1:] + ring[:1]):
            edges.setdefault((min(a, b), max(a, b)), []).append(face.normal)
    v1 = 0.0
    for (a, b), normals in edges.items():
        if len(normals) != 2:
            raise ValueError("convex hull edge is not shared by exactly two faces")
        # pi - interior dihedral angle = angle between the two outward normals.
        exterior = math.acos(max(-1.0, min(1.0, _dot(normals[0], normals[1]))))
        v1 += math.dist(points[a], points[b]) * exterior
    surface = sum(f.area for f in faces)
    volume = sum(f.area * f.offset for f in faces) / 3
    return IntrinsicVolumes(1.0, v1 / (2 * math.pi), surface / 2, volume)


def shape_vectors(pieces: Sequence[IntrinsicVolumes]) -> list[tuple[float, float, float, float]]:
    """Scale-free vectors d(P) = (V0, V1/L, sqrt(V2)/L, cbrt(V3)/L), L = (sum V3)^(1/3)."""
    scale = sum(p.v3 for p in pieces) ** (1 / 3)
    return [(p.v0, p.v1 / scale, math.sqrt(p.v2) / scale, p.v3 ** (1 / 3) / scale) for p in pieces]


def diversity(vectors: Sequence[Sequence[float]], u: float = SIMILARITY_U, q: float = DIVERSITY_ORDER) -> float:
    """Leinster-Cobbold diversity of order q with uniform weights p_i = 1/n.

    D_q = (sum_i p_i (Zp)_i^(q-1))^(1/(1-q)), with the limits
    D_1 = exp(-sum_i p_i log (Zp)_i) and D_inf = 1 / max_i (Zp)_i.
    For q = 2 this is n^2 / sum_ij Z_ij.
    """
    n = len(vectors)
    rows = [sum(math.exp(-u * math.dist(a, b)) for b in vectors) for a in vectors]
    if q == 2:  # exact closed form, so n identical pieces give exactly 1
        return n * n / sum(rows)
    zp = [r / n for r in rows]  # (Zp)_i
    top = max(zp)
    if q == math.inf:
        return 1 / top
    if q == 1:
        return math.exp(-sum(math.log(z) for z in zp) / n)
    # Factor out the largest (Zp)_i so large q cannot underflow: D_q = (1/top) * (mean (z/top)^(q-1))^(1/(1-q)).
    return (sum((z / top) ** (q - 1) for z in zp) / n) ** (1 / (1 - q)) / top


def rating(x: float) -> int:
    """Map x = log10(nodes) to a 1-5 rating (see the configuration above)."""
    if len(RATING_THRESHOLDS) != 4 or list(RATING_THRESHOLDS) != sorted(RATING_THRESHOLDS):
        raise ValueError("RATING_THRESHOLDS must be four increasing cut points")
    return 1 + sum(1 for t in RATING_THRESHOLDS if x >= t)


def piece_solid(piece: dict) -> list[Vec3]:
    """Vertices of a puzzle.json piece as the player draws it: footprint at z = 0 and its top."""
    roof = piece.get("roof")
    bottom = [(u, v, 0.0) for u, v in piece["polygon"]]
    if roof:
        top = [(u, v, roof["z0"] + roof["gx"] * u + roof["gy"] * v) for u, v in piece["polygon"]]
    else:
        top = [(u, v, float(piece["thickness"])) for u, v in piece["polygon"]]
    return bottom + top


@dataclass(frozen=True)
class Difficulty:
    n: int
    nodes: int  # a lower bound when not exhaustive
    exhaustive: bool
    solutions: int
    x: float  # log10(nodes)
    rating: int
    diversity: float  # secondary statistic


class StaleMetrics(ValueError):
    """solver-metrics.json lacks a variant or was measured on other geometry."""


def load_metrics(puzzles_dir: Path) -> dict:
    return json.loads((Path(puzzles_dir) / METRICS_FILE).read_text(encoding="utf-8"))


def search_metrics(puzzle: dict, metrics: dict) -> dict:
    """The committed search counts of this variant, refused when its geometry has changed since."""
    entry = metrics["puzzles"].get(puzzle["id"])
    rerun = "rerun generator/scripts/solver_metrics.py (see its docstring)"
    if entry is None:
        raise StaleMetrics(f"{puzzle['id']} has no entry in {METRICS_FILE}; {rerun}")
    if entry["geometryHash"] != puzzle["geometryHash"]:
        raise StaleMetrics(f"{puzzle['id']} changed geometry since it was searched; {rerun}")
    return entry


def puzzle_vectors(puzzle: dict) -> list[tuple[float, float, float, float]]:
    return shape_vectors([intrinsic_volumes(piece_solid(p)) for p in puzzle["pieces"]])


def puzzle_diversity(puzzle: dict, u: float = SIMILARITY_U, q: float = DIVERSITY_ORDER) -> float:
    return diversity(puzzle_vectors(puzzle), u, q)


def puzzle_difficulty(puzzle: dict, metrics: dict) -> Difficulty:
    entry = search_metrics(puzzle, metrics)
    x = math.log10(max(1, entry["nodes"]))
    return Difficulty(
        n=len(puzzle["pieces"]), nodes=entry["nodes"], exhaustive=entry["exhaustive"],
        solutions=entry["solutions"], x=x, rating=rating(x), diversity=puzzle_diversity(puzzle),
    )


def config(metrics: dict) -> dict:
    """The parameters as published in index.json for the explanation page."""
    solver = metrics["solver"]
    return {
        "method": "search-effort-log-nodes",
        "solver": {k: solver[k] for k in ("id", "version", "repository", "commit", "nodeLimit")},
        "thresholds": list(RATING_THRESHOLDS),
        "diversity": {
            "method": "leinster-cobbold-intrinsic-volumes",
            "u": SIMILARITY_U,
            "q": "infinity" if DIVERSITY_ORDER == math.inf else DIVERSITY_ORDER,
        },
    }
