"""Search for relief puzzles that are hard for a search with its roofs on (exploration).

Needs `maxplus_solvers` from the sibling repository tiling-solvers, like `measure_hardness.py`:

    cd ../tiling-solvers
    PYTHONPATH=../tropical-puzzle-lab/generator/src uv run --no-sync python         ../tropical-puzzle-lab/generator/scripts/lifted_search.py vertex --screen --levels 0 1         --seed 7 --columns 4 --rows 4 --mixed --samples 600 --node-limit 300000

Four commands, in the order they were tried. Each prints one JSON line per candidate,
losers included; the Pleat puzzles' provenance.md has the findings.

- `pleats`: the roof F = g(x) + h(y) on a grid of columns and rows, where g (and, for
  two-way pleats, h) is a sawtooth whose creases stand at two levels only, so whole columns
  (and rows) trade places. *Breakers* are patches max(F, d) or min(F, d) for a plane d that
  beats F only near a wall, which cut the columns at different places. Harder than cor1
  only while several assemblies remain.
- `designed`: the same with one breaker per direction, its crease placed rather than
  drawn. One assembly, but no harder than cor1: the search fills the corner with the
  fewest placements first, and a breaker is such a corner.
- `vertex`: edge-matching. Each rectangle of the grid is cut along a diagonal and every
  grid corner gets one of a few heights; each triangle's roof is the plane through its
  corners. Edge profiles then recur across the tray, and nothing stands out. With two
  levels this is the Pleat family. `--fan` cuts each rectangle into four triangles
  instead, to avoid congruent halves (slivers and many assemblies).
- `replay`: search one logged `pleats` candidate again, deeper.

Whole-search node counts do not depend on the order in which the search tries placements,
so the eight random orders that `orders` runs only matter for the first solution.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import measure_hardness as mh  # noqa: E402
from search_rational import angles_deg, signature  # noqa: E402
from tropical_puzzle_lab.export import Construction  # noqa: E402
from tropical_puzzle_lab.geometry import area, clip  # noqa: E402
from tropical_puzzle_lab.lifting import edge_to_edge  # noqa: E402
from tropical_puzzle_lab.tropical import Term, roof_transform  # noqa: E402

try:
    from maxplus_solvers import SolverConfig, solve
    from maxplus_solvers.io.tropical import import_puzzle
except ImportError as error:  # pragma: no cover
    raise SystemExit(f"needs maxplus_solvers from tiling-solvers on the path: {error}") from error

DOMAIN = F(4)
XY = F(18)
MIN_THICKNESS = F(8)
MAX_RELIEF = F(35)
TRAY_MM2 = float(2 * DOMAIN * XY) ** 2
MAX_TILT_DEG = 30.0
ORDERS = range(8)

Cell = list[tuple[F, F]]


def rect(x0: F, y0: F, x1: F, y1: F) -> Cell:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# --- the base: pleat grids -------------------------------------------------------------------


def cuts(rng: random.Random, count: int, grid: int, avoid: set[F] = frozenset()) -> list[F]:
    """`count` strips across [-4, 4] of distinct widths, on a grid of 1/`grid`, none in `avoid`.

    Column widths and row heights are kept apart so that no two rectangles are congruent.
    """
    total = int(2 * DOMAIN * grid)
    for _ in range(20_000):
        inner = sorted(rng.sample(range(1, total), count - 1))
        widths = [F(b - a, grid) for a, b in zip([0, *inner], [*inner, total])]
        if len(set(widths)) == count and min(widths) >= F(11, 20) * 2 * DOMAIN / count and not set(widths) & avoid:
            return [F(k, grid) - DOMAIN for k in [0, *inner, total]]
    raise ValueError(f"no {count} distinct widths on a grid of 1/{grid} avoid {sorted(avoid)}")


def widths(xs: list[F]) -> set[F]:
    return {b - a for a, b in zip(xs, xs[1:])}


def sawtooth(xs: list[F], amplitude: F, phase: int) -> list[F]:
    """Values at the cuts alternating between two levels: every crease is level with its kind."""
    return [amplitude * ((k + phase) % 2) for k in range(len(xs))]


def convex(ys: list[F], rng: random.Random) -> list[F]:
    """Values at the cuts of a convex profile with distinct, integer-ish slopes (cor1's rows)."""
    slopes = sorted(rng.sample(range(-4, 5), len(ys) - 1))
    values = [F(0)]
    for k, s in enumerate(slopes):
        values.append(values[-1] + F(s, 4) * (ys[k + 1] - ys[k]))
    return values


def grid_cells(xs: list[F], ys: list[F], g: list[F], h: list[F]) -> tuple[list[Term], list[Cell]]:
    terms, cells = [], []
    for j in range(len(ys) - 1):
        b = (h[j + 1] - h[j]) / (ys[j + 1] - ys[j])
        for i in range(len(xs) - 1):
            a = (g[i + 1] - g[i]) / (xs[i + 1] - xs[i])
            c = g[i] - a * xs[i] + h[j] - b * ys[j]
            terms.append(Term(f"{chr(65 + i)}{j}", a, b, c))
            cells.append(rect(xs[i], ys[j], xs[i + 1], ys[j + 1]))
    return terms, cells


# --- breakers --------------------------------------------------------------------------------


def patch(terms: list[Term], cells: list[Cell], d: Term, mode: str) -> tuple[list[Term], list[Cell]]:
    """The cells of max(F, d) (or min): each cell split where d crosses its plane."""
    sign = 1 if mode == "max" else -1
    out_terms, out_cells = [], []
    for t, cell in zip(terms, cells):
        # Where sign*(d - t) >= 0, d wins.
        normal = (sign * (d.a - t.a), sign * (d.b - t.b))
        threshold = sign * (t.c - d.c)
        won = clip(cell, normal, threshold) if normal != (0, 0) else (cell if -threshold >= 0 else [])
        kept = clip(cell, (-normal[0], -normal[1]), -threshold) if normal != (0, 0) else (cell if -threshold <= 0 else [])
        if area(won) > 0 and area(kept) > 0:
            out_terms += [t, Term(t.id + d.id, d.a, d.b, d.c)]
            out_cells += [kept, won]
        elif area(won) > 0:
            out_terms.append(Term(t.id + d.id, d.a, d.b, d.c))
            out_cells.append(won)
        else:
            out_terms.append(t)
            out_cells.append(cell)
    return out_terms, out_cells


def value(terms: list[Term], cells: list[Cell], p: tuple[F, F]) -> F:
    for t, cell in zip(terms, cells):
        if all((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0 for a, b in zip(cell, cell[1:] + cell[:1])):
            return t.value(p)
    raise ValueError(f"{p} is in no cell")


def wedge(rng: random.Random, terms: list[Term], cells: list[Cell], name: str,
          sides: tuple[int, ...] = (0, 1, 2, 3)) -> tuple[Term, str]:
    """A plane through a point on a wall, slightly above (or below) the roof there and falling
    away from the wall faster than the roof, with a tilt along the wall: it wins in a wedge."""
    # As in cor1: start at a corner, and stay close to the plane that already wins there,
    # so that the wedge is wide and gentle rather than a steep sliver.
    side = rng.choice(sides)
    s = DOMAIN - F(rng.randint(1, 8), 8)
    s = s if rng.random() < 0.5 else -s
    p = [(s, -DOMAIN), (DOMAIN, s), (s, DOMAIN), (-DOMAIN, s)][side]
    inward = [(0, 1), (-1, 0), (0, -1), (1, 0)][side]
    along = (inward[1], -inward[0])
    mode = rng.choice(["max", "min"])
    sign = 1 if mode == "max" else -1
    lift = F(rng.randint(1, 6), 10)          # how far above the roof at the wall
    fall = F(rng.randint(2, 8), 4)           # how fast it falls into the tray, per unit
    tilt = F(rng.randint(-4, 4), 4)          # slope along the wall
    base = value(terms, cells, p)
    # d(x) = F(p) + sign*(lift - fall * inward.(x - p)) + tilt * along.(x - p), plus the roof's own gradient there.
    grad = next(
        (t.a, t.b) for t, c in zip(terms, cells)
        if all((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0 for a, b in zip(c, c[1:] + c[:1]))
    )
    a = grad[0] - sign * fall * inward[0] + tilt * along[0]
    b = grad[1] - sign * fall * inward[1] + tilt * along[1]
    c = base + sign * lift - a * p[0] - b * p[1]
    return Term(name, a, b, c), mode


# --- designed breakers -----------------------------------------------------------------------
#
# Random wedges rarely meet the print limits, and two almost never do (round 2: 1 of 33).
# Here the crease of each wedge is placed, not drawn. In the bottom row the roof is
# F = g(x) + b0*y + c0; for a plane d = alpha*x + beta*y + gamma, d - F = s*(y - phi(x)) with
#
#     s = beta - b0,   phi(x) = (g(x) - alpha*x + c') / s,   c' = c0 - gamma,
#
# so the crease y = phi(x) crosses every column wall x_k at a height we can read off. It is a
# trend (alpha) plus a zigzag (g's two levels). The offset centres it in the row and the
# margin keeps it away from the row's edges, so every cut piece meets the limits by
# construction. d wins below the crease: max(F, d) when s < 0, min(F, d) when s > 0.
#
# The trend gives each column a different cut, which breaks the column swaps; the row's
# outer wall then follows d, not g, which pins the row to the tray wall. The column wedge
# does the same for the rows, inside the first column, from the top down to row j0.


def row_wedge(rng: random.Random, xs: list[F], ys: list[F], g: list[F], h: list[F], margin: F) -> tuple[Term, str] | None:
    y0, y1 = ys[0], ys[1]
    b0 = (h[1] - h[0]) / (y1 - y0)
    c0 = h[0] - b0 * y0
    alpha = F(rng.randint(-4, 4), 16)
    raw = [g[k] - alpha * xs[k] for k in range(len(xs))]
    # The crossings swing by span(raw) / |s|: take the gentlest s that fits them in the row.
    room = (y1 - y0) - 2 * margin
    if room <= 0 or len(set(raw)) < len(raw):
        return None
    s = rng.choice([-1, 1]) * (F(max(raw) - min(raw)) / room * F(rng.randint(100, 140), 100)).limit_denominator(32)
    if s == 0:
        return None
    r = [v / s for v in raw]
    if max(r) - min(r) > room:
        return None
    offset = (y0 + y1) / 2 - (max(r) + min(r)) / 2  # = c' / s
    gamma = c0 - offset * s
    return Term("a", alpha, b0 + s, gamma), ("max" if s < 0 else "min")


def column_wedge(rng: random.Random, xs: list[F], ys: list[F], g: list[F], h: list[F], margin: F) -> tuple[Term, str] | None:
    """The row wedge turned a quarter: in the first column, x = psi(y) = (h(y) - beta*y + c'') / s2,
    inside the column the whole height of the tray.

    It cannot stop part way: h zigzags, so below any row it would come back into the column
    unless its trend were too steep to print (found by trying, 434 of 441 refusals).
    """
    x0, x1 = xs[0], xs[1]
    a0 = (g[1] - g[0]) / (x1 - x0)
    e0 = g[0] - a0 * x0
    beta = F(rng.randint(-4, 4), 16)
    raw = [h[j] - beta * ys[j] for j in range(len(ys))]
    room = (x1 - x0) - 2 * margin
    if room <= 0 or len(set(raw)) < len(raw):
        return None
    s2 = rng.choice([-1, 1]) * (F(max(raw) - min(raw)) / room * F(rng.randint(100, 140), 100)).limit_denominator(32)
    if s2 == 0:
        return None
    q = [v / s2 for v in raw]
    if max(q) - min(q) > room:
        return None
    offset = (x0 + x1) / 2 - (max(q) + min(q)) / 2  # = c'' / s2
    return Term("b", a0 + s2, beta, e0 - offset * s2), ("max" if s2 < 0 else "min")


def widest_first(xs: list[F]) -> list[F]:
    """The same strips, the widest moved to the start: the wedges get the most room.

    Strip order does not change the rivals, which permute strips anyway.
    """
    w = [b - a for a, b in zip(xs, xs[1:])]
    w.insert(0, w.pop(w.index(max(w))))
    out = [xs[0]]
    for v in w:
        out.append(out[-1] + v)
    return out


MIN_PIECE_MM2 = F(260)


def turn(terms: list[Term], cells: list[Cell], quarters: int) -> tuple[list[Term], list[Cell]]:
    """The design turned by quarter turns about the tray centre: R(x, y) = (-y, x).

    A roof F moves to F(R^-1 p), and R^-1 (x, y) = (y, -x), so (a, b) becomes (-b, a).
    Turning keeps the cells counter-clockwise.
    """
    for _ in range(quarters % 4):
        terms = [Term(t.id, -t.b, t.a, t.c) for t in terms]
        cells = [[(-y, x) for x, y in cell] for cell in cells]
    return terms, cells


def where_won(terms: list[Term], suffix: str) -> set[str]:
    """The grid cells (column letter and row digit) a breaker took part of."""
    return {t.id[:2] for t in terms if t.id.endswith(suffix) or suffix in t.id[2:]}


def run_designed(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    margin = F(args.margin_mm) / XY
    for sample in range(args.samples):
        row: dict = {"sample": sample, "family": "designed"}
        for attempt in range(args.attempts):
            while True:
                xs = cuts(rng, args.columns, args.grid)
                try:
                    ys = cuts(rng, args.rows, args.row_grid, avoid=widths(xs))
                    break
                except ValueError:
                    continue
            xs, ys = widest_first(xs), widest_first(ys)
            g = sawtooth(xs, F(1), rng.randrange(2))
            h = sawtooth(ys, F(rng.randint(2, 5), 4), rng.randrange(2))
            # Margins by area too: both parts of a cut cell keep at least MIN_PIECE_MM2.
            row_margin = max(margin, MIN_PIECE_MM2 / (min(widths(xs)) * XY) / XY)
            column_margin = max(margin, MIN_PIECE_MM2 / (min(widths(ys)) * XY) / XY)
            first = row_wedge(rng, xs, ys, g, h, row_margin)
            second = column_wedge(rng, xs, ys, g, h, column_margin)
            if first is None or second is None:
                continue
            terms, cells = grid_cells(xs, ys, g, h)
            terms, cells = patch(terms, cells, first[0], first[1])
            terms, cells = patch(terms, cells, second[0], second[1])
            # Each wedge must have stayed where it was put: the bottom row, the first column.
            if not where_won(terms, "a") <= {f"{chr(65 + i)}0" for i in range(args.columns)}:
                continue
            if not where_won(terms, "b") <= {f"A{j}" for j in range(args.rows)}:
                continue
            terms, cells = turn(terms, cells, args.turns)
            info, relief = limits(terms, cells)
            if info["ok"]:
                break
        else:
            print(json.dumps({**row, "found": False}), flush=True)
            continue
        row["attempts"] = attempt + 1
        recipe = recipe_of(terms, cells, relief)
        try:
            Construction(recipe).check()
            measured = mh.measure(recipe, node_limit=args.node_limit)
        except (AssertionError, ValueError) as error:
            print(json.dumps({**row, "error": str(error)}), flush=True)
            continue
        row.update(info, **measured)
        if measured["solutions"] == 1 and measured["whole"]:
            row.update(orders(recipe, args.node_limit))
        row["design"] = {
            "xs": [str(x) for x in xs], "ys": [str(y) for y in ys], "g": [str(v) for v in g], "h": [str(v) for v in h],
            "breakers": [{"mode": m, "a": str(d.a), "b": str(d.b), "c": str(d.c)} for d, m in (first[:2], second[:2])],
        }
        print(json.dumps(row), flush=True)


# --- edge-matching: vertex heights on a triangulated grid -------------------------------------
#
# The fewest-candidates rule puts down whatever stands out first, so a breaker is found at
# once (designed wedges: one assembly, about 1 300 nodes, dead ends 6 deep). Here nothing
# stands out: every grid vertex gets a height from a few levels, and each rectangle is cut
# along a diagonal into two triangles, each under the plane through its corners. On a
# triangulation any vertex heights are a lifting. An edge's profile is its length (a
# column width, a row height, or a cell's diagonal) and a pair of levels: a colour, as in
# edge-matching puzzles, which recurs across the tray.


def plane(p: tuple[F, F], q: tuple[F, F], r: tuple[F, F], hp: F, hq: F, hr: F, name: str) -> Term:
    """The affine a*x + b*y + c through three points at given heights (Cramer's rule)."""
    det = (q[0] - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (q[1] - p[1])
    a = ((hq - hp) * (r[1] - p[1]) - (hr - hp) * (q[1] - p[1])) / det
    b = ((q[0] - p[0]) * (hr - hp) - (r[0] - p[0]) * (hq - hp)) / det
    return Term(name, a, b, hp - a * p[0] - b * p[1])


def triangulated(xs: list[F], ys: list[F], heights: list[list[F]], diagonals: list[list[int]]) -> tuple[list[Term], list[Cell]]:
    terms, cells = [], []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            corners = {(di, dj): ((xs[i + di], ys[j + dj]), heights[i + di][j + dj]) for di in (0, 1) for dj in (0, 1)}
            if diagonals[i][j] == 0:  # from bottom left to top right
                halves = (((0, 0), (1, 0), (1, 1)), ((0, 0), (1, 1), (0, 1)))
            else:  # from bottom right to top left
                halves = (((0, 0), (1, 0), (0, 1)), ((1, 0), (1, 1), (0, 1)))
            for k, half in enumerate(halves):
                (p, hp), (q, hq), (r, hr) = (corners[c] for c in half)
                terms.append(plane(p, q, r, hp, hq, hr, f"{chr(65 + i)}{j}{'lu'[k]}"))
                cells.append([p, q, r])
    return terms, cells


def fanned(xs: list[F], ys: list[F], heights: list[list[F]], diagonals: list[list[int]],
           points: list[list[tuple[F, F]]]) -> tuple[list[Term], list[Cell]]:
    """Each rectangle cut into four triangles from a point on its diagonal, at a height of its own.

    Off the centre, the four are not congruent, and no triangle is congruent to its cell's
    other half, as the two halves of a diagonal cut always are.
    """
    terms, cells = [], []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            t, hp = points[i][j]
            corners = [((xs[i + di], ys[j + dj]), heights[i + di][j + dj]) for di, dj in ((0, 0), (1, 0), (1, 1), (0, 1))]
            a, b = (corners[0], corners[2]) if diagonals[i][j] == 0 else (corners[1], corners[3])
            p = (a[0][0] + t * (b[0][0] - a[0][0]), a[0][1] + t * (b[0][1] - a[0][1]))
            for k in range(4):
                (q, hq), (r, hr) = corners[k], corners[(k + 1) % 4]
                terms.append(plane(q, r, p, hq, hr, hp, f"{chr(65 + i)}{j}{'srne'[k]}"))
                cells.append([q, r, p])
    return terms, cells


def run_vertex(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    levels = [F(v) for v in args.levels]
    for sample in range(args.samples):
        while True:
            xs = cuts(rng, args.columns, args.grid)
            try:
                ys = cuts(rng, args.rows, args.row_grid, avoid=widths(xs))
                break
            except ValueError:
                continue
        heights = [[rng.choice(levels) for _ in ys] for _ in xs]
        diagonals = [[rng.randrange(2) if args.mixed else 0 for _ in ys[:-1]] for _ in xs[:-1]]
        if args.fan:
            points = [[(F(rng.choice([2, 3])) / 5 if rng.randrange(2) else F(rng.choice([3, 2])) / 5 + F(1, 5), rng.choice(levels))
                       for _ in ys[:-1]] for _ in xs[:-1]]
            terms, cells = fanned(xs, ys, heights, diagonals, points)
        else:
            terms, cells = triangulated(xs, ys, heights, diagonals)
        info, relief = limits(terms, cells)
        row: dict = {"sample": sample, "family": "vertex", **info}
        recipe = recipe_of(terms, cells, relief)
        if args.screen and not info["okTwins"]:
            continue
        try:
            Construction(recipe).check()
            row.update(mh.measure(recipe, node_limit=args.node_limit))
        except (AssertionError, ValueError) as error:
            row["error"] = str(error)
        row["design"] = {"xs": [str(x) for x in xs], "ys": [str(y) for y in ys],
                         "heights": [[str(h) for h in col] for col in heights], "diagonals": diagonals}
        print(json.dumps(row), flush=True)


# --- the candidate as a recipe, and its limits ----------------------------------------------


def recipe_of(terms: list[Term], cells: list[Cell], relief: F, name: str = "candidate") -> dict:
    return {
        "formatVersion": 1, "family": "lifted", "id": name, "revision": 1,
        "name": {"shape": "Pleat", "letter": "z"},
        "domain": str(DOMAIN), "xyMmPerUnit": str(XY), "minThicknessMm": str(MIN_THICKNESS),
        "reliefMm": str(relief), "trayRimMm": "7",
        "cells": [
            {"id": t.id, "vertices": [[str(x), str(y)] for x, y in cell],
             "roof": {"a": str(F(t.a)), "b": str(F(t.b)), "c": str(t.c)}}
            for t, cell in zip(terms, cells)
        ],
        "validation": mh.VALIDATION, "scramble": {"algorithm": "v1", "defaultSeed": 1}, "source": {},
    }


def limits(terms: list[Term], cells: list[Cell]) -> tuple[dict, F]:
    """The print limits of search_rational and corrugated, and the largest relief within the tilt limit."""
    mm = [[(float(x * XY), float(y * XY)) for x, y in c] for c in cells]
    areas = [float(area(c) * XY * XY) / TRAY_MM2 for c in cells]
    min_angle = min(min(angles_deg(p)) for p in mm)
    min_edge = min(math.dist(p[k], p[(k + 1) % len(p)]) for p in mm for k in range(len(p)))
    roof = roof_transform(terms, cells, MIN_THICKNESS, F(1))
    steepest = max(math.hypot(float(t.a), float(t.b)) for t in terms) / float(XY)
    # Tilt of relief R: atan(R * scale1 * |g| / XY), scale1 = 1 / (f_max - f_min).
    relief = min(MAX_RELIEF, F(math.tan(math.radians(MAX_TILT_DEG)) / (float(roof.scale) * steepest)).limit_denominator(4))
    found = {
        "pieces": len(cells), "minArea": round(min(areas), 4), "maxArea": round(max(areas), 4),
        "minAngle": round(min_angle, 1), "minEdgeMm": round(min_edge, 1), "reliefMm": float(relief),
        "congruent": len({signature(p) for p in mm}) < len(mm), "edgeToEdge": edge_to_edge(cells),
    }
    # A breaker that wins over much of the tray leaves one plane under many pieces: a tilted
    # flat puzzle, hard for the wrong reason (round 1, two-way sample 10: 25 of 30 pieces).
    planes: dict[tuple[F, F, F], float] = {}
    for t, a_ in zip(terms, areas):
        key = (F(t.a), F(t.b), t.c)
        planes[key] = planes.get(key, 0.0) + a_
    found["largestPlane"] = round(max(planes.values()), 3)
    shapes: dict = {}
    for poly in mm:
        shapes[signature(poly)] = shapes.get(signature(poly), 0) + 1
    found["twinMax"] = max(shapes.values())
    # Edge-matching grids: a rectangle's two halves are always congruent, so pairs are allowed.
    found["okTwins"] = (min(areas) >= 0.012 and max(areas) <= 0.15 and min_angle >= 20 and min_edge >= 6
                        and found["twinMax"] <= 2 and relief >= 12 and found["largestPlane"] <= 0.2)
    found["ok"] = (min(areas) >= 0.012 and max(areas) <= 0.15 and min_angle >= 20 and min_edge >= 6
                   and not found["congruent"] and relief >= 12 and found["largestPlane"] <= 0.2)
    return found, relief


# --- measuring -------------------------------------------------------------------------------


def orders(recipe: dict, node_limit: int) -> dict:
    instance, _ = import_puzzle(mh.relief_document(recipe), seed=1, commit="exploration")
    nodes = []
    for seed in ORDERS:
        config = SolverConfig(mh.SOLVER, mode=instance.regime, max_solutions=None, seed=seed,
                              options={"node_limit": node_limit, "order": "random"})
        result = solve(instance, config)
        nodes.append(result.metrics["nodes"] if result.exhaustive else node_limit)
    e2e = solve(instance, SolverConfig(mh.SOLVER, mode=instance.regime, max_solutions=None,
                                       assumptions=("edge-to-edge",), options={"node_limit": node_limit}))
    return {"medianNodes": statistics.median(nodes), "orderNodes": nodes,
            "e2eNodes": e2e.metrics["nodes"], "e2eSolutions": len(e2e.solutions)}


def run_pleats(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    for sample in range(args.samples):
        while True:
            xs = cuts(rng, args.columns, args.grid)
            try:
                ys = cuts(rng, args.rows, args.row_grid, avoid=widths(xs))
                break
            except ValueError:
                continue  # these columns leave no row heights apart from them: draw again
        g = sawtooth(xs, F(1), rng.randrange(2))
        h = sawtooth(ys, F(rng.randint(2, 5), 4), rng.randrange(2)) if args.two_way else convex(ys, rng)
        base = grid_cells(xs, ys, g, h)
        count = rng.randint(args.breakers[0], args.breakers[1])
        row: dict = {"sample": sample, "twoWay": args.two_way, "breakers": count}
        # Breakers are drawn until the pieces they cut meet the print limits.
        for attempt in range(args.attempts):
            terms, cells = base
            breakers = []
            for k in range(count):
                # With --crosswise, alternate walls: bottom or top (across the columns), then a side (across the rows).
                sides = ((0, 2), (1, 3))[k % 2] if args.crosswise else (0, 1, 2, 3)
                d, mode = wedge(rng, terms, cells, "abcdefgh"[k], sides)
                terms, cells = patch(terms, cells, d, mode)
                breakers.append({"mode": mode, "a": str(d.a), "b": str(d.b), "c": str(d.c)})
            info, relief = limits(terms, cells)
            if info["ok"]:
                break
        row["attempts"] = attempt + 1
        if not info["ok"]:
            print(json.dumps({**row, **info}), flush=True)
            continue
        recipe = recipe_of(terms, cells, relief)
        try:
            Construction(recipe).check()
            measured = mh.measure(recipe, node_limit=args.node_limit)
        except (AssertionError, ValueError) as error:
            print(json.dumps({**row, "error": str(error)}), flush=True)
            continue
        row.update(info, **measured)
        if measured["solutions"] == 1 and measured["whole"]:
            row.update(orders(recipe, args.node_limit))
        row["design"] = {"xs": [str(x) for x in xs], "ys": [str(y) for y in ys],
                         "g": [str(v) for v in g], "h": [str(v) for v in h], "breakers": breakers}
        print(json.dumps(row), flush=True)


def rebuild(design: dict) -> tuple[list[Term], list[Cell]]:
    """A candidate's cells and roofs from the `design` it was logged with."""
    xs, ys = [F(v) for v in design["xs"]], [F(v) for v in design["ys"]]
    terms, cells = grid_cells(xs, ys, [F(v) for v in design["g"]], [F(v) for v in design["h"]])
    for k, b in enumerate(design["breakers"]):
        terms, cells = patch(terms, cells, Term("abcdefgh"[k], F(b["a"]), F(b["b"]), F(b["c"])), b["mode"])
    return terms, cells


def run_replay(args: argparse.Namespace) -> None:
    """Search one logged candidate again, deeper; optionally write its recipe."""
    rows = [json.loads(line) for line in Path(args.results).read_text(encoding="utf-8").splitlines() if line.startswith("{")]
    row = next(r for r in rows if r.get("sample") == args.sample and "design" in r)
    terms, cells = rebuild(row["design"])
    _, relief = limits(terms, cells)
    recipe = recipe_of(terms, cells, relief, name=args.name)
    if args.recipe:
        Path(args.recipe).write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
    out = {"sample": args.sample, **mh.measure(recipe, node_limit=args.node_limit)}
    if out["whole"] and out["solutions"] == 1:
        out.update(orders(recipe, args.node_limit))
    print(json.dumps(out), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    pleats = commands.add_parser("pleats", help="pleat grids with wedge breakers")
    pleats.add_argument("--seed", type=int, default=1)
    pleats.add_argument("--samples", type=int, default=20)
    pleats.add_argument("--columns", type=int, default=5)
    pleats.add_argument("--rows", type=int, default=5)
    pleats.add_argument("--grid", type=int, default=8, help="columns on a grid of 1/GRID units")
    pleats.add_argument("--row-grid", type=int, default=6, help="rows on a grid of 1/ROW_GRID units")
    pleats.add_argument("--two-way", action="store_true")
    pleats.add_argument("--breakers", type=int, nargs=2, default=(1, 2))
    pleats.add_argument("--node-limit", type=int, default=300_000)
    pleats.add_argument("--attempts", type=int, default=400, help="breaker draws per grid")
    pleats.add_argument("--crosswise", action="store_true", help="alternate breakers between the two directions")
    designed = commands.add_parser("designed", help="two-way pleats with one designed wedge per direction")
    designed.add_argument("--seed", type=int, default=1)
    designed.add_argument("--samples", type=int, default=20)
    designed.add_argument("--columns", type=int, default=5)
    designed.add_argument("--rows", type=int, default=5)
    designed.add_argument("--grid", type=int, default=8)
    designed.add_argument("--row-grid", type=int, default=6)
    designed.add_argument("--margin-mm", type=int, default=6, help="how far a crease stays from a row or column edge")
    designed.add_argument("--attempts", type=int, default=2000)
    designed.add_argument("--turns", type=int, default=0, help="quarter turns of the finished design")
    designed.add_argument("--node-limit", type=int, default=300_000)
    vertex = commands.add_parser("vertex", help="edge-matching: vertex heights on a triangulated grid")
    vertex.add_argument("--seed", type=int, default=1)
    vertex.add_argument("--samples", type=int, default=10)
    vertex.add_argument("--columns", type=int, default=4)
    vertex.add_argument("--rows", type=int, default=4)
    vertex.add_argument("--grid", type=int, default=8)
    vertex.add_argument("--row-grid", type=int, default=6)
    vertex.add_argument("--levels", type=int, nargs="+", default=[0, 1])
    vertex.add_argument("--mixed", action="store_true", help="choose each cell's diagonal at random")
    vertex.add_argument("--fan", action="store_true", help="four triangles per cell from a point on its diagonal")
    vertex.add_argument("--screen", action="store_true", help="search only designs within the limits (twins allowed)")
    vertex.add_argument("--node-limit", type=int, default=200_000)
    replay = commands.add_parser("replay", help="search one logged candidate again")
    replay.add_argument("results", help="a JSON-lines file written by 'pleats'")
    replay.add_argument("--sample", type=int, required=True)
    replay.add_argument("--node-limit", type=int, default=3_000_000)
    replay.add_argument("--name", default="candidate")
    replay.add_argument("--recipe", help="also write the recipe here")
    args = parser.parse_args()
    {"pleats": run_pleats, "designed": run_designed, "vertex": run_vertex, "replay": run_replay}[args.command](args)


if __name__ == "__main__":
    main()
