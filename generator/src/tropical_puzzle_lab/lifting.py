"""Liftings of a polygonal subdivision, and the conditions rival assemblies put on them.

A *lifting* of a subdivision of the tray into convex cells is a roof that is
affine on each cell and continuous across every shared edge: one affine
function (a, b, c), height a*x + b*y + c, per cell. Continuity along a shared
stretch is equality at its two ends, because the difference of two affine
functions is affine along a segment. So the liftings form a linear space, the
null space of those equations.

By the Maxwell–Cremona correspondence, a lifting modulo the global affine
functions is a self-stress of the subdivision's interior edges: across each
edge the jump in gradient is normal to it, g_i - g_j = w * n, and the weights
w are in equilibrium at every interior vertex. The space therefore has
dimension 3 plus the number of independent stresses. A line cut has one; a
cross has two; the pinwheel (four rectangles round a square) has none, which
is the classic subdivision with no lifting but the flat ones.

A *rival* is another assembly of the same cells: a rigid motion of each cell
such that the moved cells tile the tray again. A roof that is continuous in
the rival as well satisfies more linear equations, one pair per seam of the
rival. Choosing a lifting that a rival satisfies on all seams but a few is how
near-symmetric puzzles are designed (`scripts/lifted_search.py`).

Everything is exact, on `Fraction`s.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from .geometry import Point, Polygon, area, intersect

Vector = list[Fraction]
# One row of a linear system: coefficients over the 3n unknowns (a_0, b_0, c_0, a_1, ...).
Row = list[Fraction]


@dataclass(frozen=True)
class Seam:
    """A shared stretch [p, q] of the boundaries of cells i and j (i < j)."""

    i: int
    j: int
    p: Point
    q: Point


@dataclass(frozen=True)
class Motion:
    """A rigid motion w = R p + t with R a rotation given by exact (cos, sin)."""

    cos: Fraction
    sin: Fraction
    tx: Fraction
    ty: Fraction

    def __post_init__(self) -> None:
        if self.cos * self.cos + self.sin * self.sin != 1:
            raise ValueError("a motion must rotate by an exact rotation: cos² + sin² = 1")

    def apply(self, p: Point) -> Point:
        return (self.cos * p[0] - self.sin * p[1] + self.tx, self.sin * p[0] + self.cos * p[1] + self.ty)


IDENTITY = Motion(Fraction(1), Fraction(0), Fraction(0), Fraction(0))


def translation(tx, ty) -> Motion:
    return Motion(Fraction(1), Fraction(0), Fraction(tx), Fraction(ty))


def quarter_turn(k: int, about: Point = (Fraction(0), Fraction(0))) -> Motion:
    """Rotation by k quarter turns about a point."""
    cos, sin = [(1, 0), (0, 1), (-1, 0), (0, -1)][k % 4]
    cx, cy = about
    # w = R (p - c) + c
    return Motion(Fraction(cos), Fraction(sin), cx - (cos * cx - sin * cy), cy - (sin * cx + cos * cy))


# --- segments -------------------------------------------------------------------------------


def _cross(o: Point, a: Point, b: Point) -> Fraction:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _edges(poly: Polygon) -> list[tuple[Point, Point]]:
    return list(zip(poly, poly[1:] + poly[:1]))


def _shared(e: tuple[Point, Point], f: tuple[Point, Point]) -> tuple[Point, Point] | None:
    """The stretch two collinear edges share, if it has positive length."""
    (p, q), (r, s) = e, f
    if _cross(p, q, r) != 0 or _cross(p, q, s) != 0:
        return None
    d = (q[0] - p[0], q[1] - p[1])
    length2 = d[0] * d[0] + d[1] * d[1]

    def t(x: Point) -> Fraction:
        return ((x[0] - p[0]) * d[0] + (x[1] - p[1]) * d[1]) / length2

    lo, hi = max(Fraction(0), min(t(r), t(s))), min(Fraction(1), max(t(r), t(s)))
    if lo >= hi:
        return None
    return (p[0] + d[0] * lo, p[1] + d[1] * lo), (p[0] + d[0] * hi, p[1] + d[1] * hi)


def seams(cells: Sequence[Polygon]) -> list[Seam]:
    """Every stretch two cells share, T-junctions included."""
    found = []
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            for e in _edges(cells[i]):
                for f in _edges(cells[j]):
                    stretch = _shared(e, f)
                    if stretch is not None:
                        found.append(Seam(i, j, *stretch))
    return found


def edge_to_edge(cells: Sequence[Polygon]) -> bool:
    """True when no vertex of any cell lies inside an edge of another (no T-junction)."""
    for i, cell in enumerate(cells):
        for j, other in enumerate(cells):
            if i == j:
                continue
            for v in cell:
                for p, q in _edges(other):
                    if v in (p, q) or _cross(p, q, v) != 0:
                        continue
                    if min(p[0], q[0]) <= v[0] <= max(p[0], q[0]) and min(p[1], q[1]) <= v[1] <= max(p[1], q[1]):
                        return False
    return True


def tiles(cells: Sequence[Polygon], target: Polygon) -> bool:
    """True when the cells cover the target without overlap (exact areas)."""
    if sum((area(c) for c in cells), Fraction(0)) != area(target):
        return False
    if any(area(intersect(c, target)) != area(c) for c in cells):
        return False
    return all(area(intersect(cells[i], cells[j])) == 0 for i in range(len(cells)) for j in range(i))


# --- linear algebra -------------------------------------------------------------------------


def _row(n: int, entries: dict[int, Fraction]) -> Row:
    row = [Fraction(0)] * (3 * n)
    for k, v in entries.items():
        row[k] += v
    return row


def _height_row(n: int, cell: int, motion: Motion, w: Point, sign: int) -> dict[int, Fraction]:
    """Coefficients of ``sign`` times the height at world point w of ``cell`` moved by ``motion``.

    The moved roof at w is the original roof at p = R^T (w - t): a*p_x + b*p_y + c.
    """
    dx, dy = w[0] - motion.tx, w[1] - motion.ty
    px = motion.cos * dx + motion.sin * dy
    py = -motion.sin * dx + motion.cos * dy
    return {3 * cell: sign * px, 3 * cell + 1: sign * py, 3 * cell + 2: Fraction(sign)}


def _merge(*parts: dict[int, Fraction]) -> dict[int, Fraction]:
    out: dict[int, Fraction] = {}
    for part in parts:
        for k, v in part.items():
            out[k] = out.get(k, Fraction(0)) + v
    return out


def continuity_rows(cells: Sequence[Polygon], motions: Sequence[Motion] | None = None) -> list[Row]:
    """Two equations per seam of the (moved) cells: equal heights at both ends."""
    n = len(cells)
    motions = list(motions) if motions is not None else [IDENTITY] * n
    moved = [[m.apply(v) for v in cell] for cell, m in zip(cells, motions)]
    rows = []
    for seam in seams(moved):
        for w in (seam.p, seam.q):
            rows.append(_row(n, _merge(_height_row(n, seam.i, motions[seam.i], w, 1),
                                       _height_row(n, seam.j, motions[seam.j], w, -1))))
    return rows


def null_space(rows: Sequence[Row], width: int) -> list[Vector]:
    """An exact basis of {v : row . v = 0 for every row}, by reduced row echelon form."""
    matrix = [list(r) for r in rows if any(r)]
    pivots: list[int] = []
    rank = 0
    for col in range(width):
        pivot = next((r for r in range(rank, len(matrix)) if matrix[r][col] != 0), None)
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        lead = matrix[rank][col]
        matrix[rank] = [v / lead for v in matrix[rank]]
        for r in range(len(matrix)):
            if r != rank and matrix[r][col] != 0:
                f = matrix[r][col]
                matrix[r] = [a - f * b for a, b in zip(matrix[r], matrix[rank])]
        pivots.append(col)
        rank += 1
        if rank == len(matrix):
            break
    free = [c for c in range(width) if c not in pivots]
    basis = []
    for f in free:
        v = [Fraction(0)] * width
        v[f] = Fraction(1)
        for r, p in enumerate(pivots):
            v[p] = -matrix[r][f]
        basis.append(v)
    return basis


def lifting_space(cells: Sequence[Polygon]) -> list[Vector]:
    """A basis of the liftings: vectors (a_0, b_0, c_0, a_1, ...) of continuous roofs."""
    return null_space(continuity_rows(cells), 3 * len(cells))


def rival_space(cells: Sequence[Polygon], rivals: Sequence[Sequence[Motion]], exempt=()) -> list[Vector]:
    """The liftings that are also continuous in every rival, except on the exempt seams.

    ``exempt`` lists (rival index, seam) pairs, seams as `seams` returns them for
    that rival's moved cells: the breakers, where the rival is allowed to fail.
    """
    rows = continuity_rows(cells)
    skip = set(exempt)
    for k, motions in enumerate(rivals):
        moved = [[m.apply(v) for v in cell] for cell, m in zip(cells, motions)]
        n = len(cells)
        for seam in seams(moved):
            if (k, seam) in skip:
                continue
            for w in (seam.p, seam.q):
                rows.append(_row(n, _merge(_height_row(n, seam.i, motions[seam.i], w, 1),
                                           _height_row(n, seam.j, motions[seam.j], w, -1))))
    return null_space(rows, 3 * len(cells))


def satisfies(rows: Sequence[Row], v: Vector) -> bool:
    return all(sum((a * b for a, b in zip(r, v)), Fraction(0)) == 0 for r in rows)


# --- Maxwell–Cremona ------------------------------------------------------------------------


def stress_of(cells: Sequence[Polygon], v: Vector) -> dict[Seam, Fraction]:
    """The stress of a lifting: the weight w with g_i - g_j = w * n on each seam, n = (q - p) turned left.

    Raises if a gradient jump is not normal to its seam, which a lifting never has.
    """
    out = {}
    for seam in seams(cells):
        gi = (v[3 * seam.i], v[3 * seam.i + 1])
        gj = (v[3 * seam.j], v[3 * seam.j + 1])
        jump = (gi[0] - gj[0], gi[1] - gj[1])
        d = (seam.q[0] - seam.p[0], seam.q[1] - seam.p[1])
        if jump[0] * d[0] + jump[1] * d[1] != 0:
            raise ValueError(f"cells {seam.i} and {seam.j}: the gradient jump is not normal to their seam")
        n = (-d[1], d[0])
        out[seam] = (jump[0] * n[0] + jump[1] * n[1]) / (n[0] * n[0] + n[1] * n[1])
    return out


def creases(cells: Sequence[Polygon], v: Vector) -> list[Seam]:
    """The seams where the lifting bends (non-zero stress)."""
    return [seam for seam, w in stress_of(cells, v).items() if w != 0]
