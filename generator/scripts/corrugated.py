"""Corrugated roofs: relief puzzles that are hard for a search with their roofs on.

Exploration, run like `measure_hardness.py` (it needs `maxplus_solvers` from tiling-solvers):

    cd ../tiling-solvers
    PYTHONPATH=../tropical-puzzle-lab/generator/src uv run --no-sync python \
        ../tropical-puzzle-lab/generator/scripts/corrugated.py --seed 1 --trials 300

The roof is F(x, y) = g(x) + h(y) plus a few extra terms. g is a sawtooth whose valleys all
stand at one height and whose ridges all stand at another; h is convex. Along a valley or a
ridge line of g the roof is h(y) plus a constant, the same on every such line, so in one row
every edge on a valley line has the same height profile, and likewise on a ridge line. The
roofs then do not say which tooth stands next to which. The teeth have different slopes and
so different widths, which keeps the pieces from being congruent. On its own this roof has
many assemblies (whole columns can change places); extra terms that cut creases across
several columns are searched for, and a candidate is kept when it has one assembly.

Tilt is the constraint. With the relief fixed at 35 mm in a 144 mm tray, the more teeth
there are and the higher they stand, the steeper their sides. `--max-tilt` (30 degrees, the
limit for printing roof-down) bounds it; `--teeth` and `--tooth-share` say how many
half-teeth to try and what share of the relief the sawtooth may take.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import sys
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import measure_hardness as mh  # noqa: E402
import search_rational as sr  # noqa: E402
from tropical_puzzle_lab.export import Construction  # noqa: E402
from tropical_puzzle_lab.tropical import Term, tropical_value  # noqa: E402

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def parts(widths: list[F], slopes: list[int]) -> tuple[list, list]:
    """A piecewise linear function on [-4, 4] as two convex ones: f = max(first) - max(second), lines as (slope, intercept)."""
    assert sum(widths) == 8 and len(widths) == len(slopes)
    x = F(-4)
    p, q = slopes[0], 0
    cp, cq = -p * x, F(0)  # both parts are 0 at x = -4
    first, second = [(p, cp)], [(q, cq)]
    for k in range(1, len(slopes)):
        x += widths[k - 1]
        jump = slopes[k] - slopes[k - 1]
        if jump > 0:
            value = p * x + cp
            p += jump
            cp = value - p * x
            first.append((p, cp))
        elif jump < 0:
            value = q * x + cq
            q -= jump
            cq = value - q * x
            second.append((q, cq))
    return first, second


def terms_of(xw, xs, yw, ys, extra_p=(), extra_q=()) -> tuple[list[Term], list[Term]]:
    px, qx = parts(xw, xs)
    py, qy = parts(yw, ys)
    num = [Term("", a, b, c + d) for a, c in px for b, d in py] + [Term("", *t) for t in extra_p]
    den = [Term("", a, b, c + d) for a, c in qx for b, d in qy] + [Term("", *t) for t in extra_q]
    return (
        [Term(LETTERS[i], t.a, t.b, t.c) for i, t in enumerate(num)],
        [Term(LETTERS[i].lower(), t.a, t.b, t.c) for i, t in enumerate(den)],
    )


def sawtooth(slopes: list[int]) -> tuple[list[F], list[int]]:
    """Half-teeth with the given steepnesses, alternately up and down, all of one height, filling the width 8."""
    height = F(8) / sum(F(1, s) for s in slopes)
    return [height / s for s in slopes], [s if k % 2 == 0 else -s for k, s in enumerate(slopes)]


def physical(num: list[Term], den: list[Term]) -> dict:
    m = sr.climb_metrics(num, den)
    return {
        "maxTiltDeg": round(m["maxTiltDeg"], 1), "minAreaShare": round(m["minArea"], 4), "minEdgeMm": round(m["minEdgeMm"], 1),
        "minAngleDeg": round(m["minAngle"], 1), "congruent": m["congruent"], "heightIqrMm": round(m["heightIqrMm"], 1),
    }


def tooth_height_mm(num: list[Term], den: list[Term], xw: list[F], xs: list[int]) -> float:
    c = Construction(mh.recipe_of(num, den))
    return float(c.roof.scale * xw[0] * abs(xs[0]))


def row_layouts(args: argparse.Namespace):
    """Rows: convex profiles of two to five rows, and with `--both` a second sawtooth."""
    yield [F(4), F(4)], [0, 1]
    yield [F(5), F(3)], [0, 1]
    yield [F(3), F(3), F(2)], [0, 1, 2]
    yield [F(5, 2), F(3), F(5, 2)], [0, 1, 2]
    # Rows of different heights, so that no two pieces of a column have the same footprint.
    yield [F(9, 4), F(17, 8), F(15, 8), F(7, 4)], [0, 1, 2, 3]
    yield [F(9, 5), F(17, 10), F(8, 5), F(3, 2), F(7, 5)], [0, 1, 2, 3, 4]
    if args.both:
        for count in (3, 4):
            for slopes in itertools.combinations(args.steepness, count):
                yield sawtooth(list(slopes))


def profile_range(widths: list[F], slopes: list[int]) -> F:
    """Largest minus smallest value of the piecewise linear function with these pieces."""
    value, low, high = F(0), F(0), F(0)
    for w, s in zip(widths, slopes):
        value += w * s
        low, high = min(low, value), max(high, value)
    return high - low


def tilt_deg(xw, xs, yw, ys) -> tuple[float, float]:
    """(steepest roof tilt in degrees, sawtooth height in mm) of g(x) + h(y), without building the cells.

    The range of a sum of a function of x and a function of y is the sum of their ranges, and
    every column meets every row, so the steepest piece has the steepest slope of each.
    """
    scale = float(sr.RELIEF) / float(profile_range(xw, xs) + profile_range(yw, ys))
    steepest = math.hypot(max(abs(s) for s in xs), max(abs(s) for s in ys))
    return math.degrees(math.atan(scale * steepest / sr.XY)), scale * float(xw[0] * abs(xs[0]))


def bases(args: argparse.Namespace):
    """Sawtooth-by-rows roofs within the tilt limit."""
    for count in args.teeth:
        for slopes in itertools.combinations(args.steepness, count):
            xw, xs = sawtooth(list(slopes))
            for yw, base in row_layouts(args):
                for k in args.row_scale:
                    ys = [s * k for s in base]
                    tilt, height = tilt_deg(xw, xs, yw, ys)
                    if tilt > args.max_tilt or height < args.min_tooth_mm:
                        continue
                    yield {"xw": xw, "xs": xs, "yw": yw, "ys": ys, "toothMm": round(height, 1), "maxTiltDeg": round(tilt, 1)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--trials", type=int, default=200, help="extra-term draws per base")
    parser.add_argument("--bases", type=int, default=6, help="how many bases to search, tallest teeth first")
    parser.add_argument("--teeth", type=int, nargs="+", default=[4, 5, 6], help="numbers of half-teeth to try")
    parser.add_argument("--steepness", type=int, nargs="+", default=[2, 3, 4, 5, 6], help="slopes a half-tooth may have")
    parser.add_argument("--row-scale", type=int, nargs="+", default=[1, 2, 3, 4, 6, 8], help="multipliers for the rows' slopes")
    parser.add_argument("--max-tilt", type=float, default=30.0)
    parser.add_argument("--min-tooth-mm", type=float, default=6.0, help="least height of the sawtooth, mm")
    parser.add_argument("--min-edge", type=float, default=6.0)
    parser.add_argument("--min-area", type=float, default=0.012)
    parser.add_argument("--min-angle", type=float, default=20.0)
    parser.add_argument("--max-pieces", type=int, default=26)
    parser.add_argument("--node-limit", type=int, default=300_000)
    parser.add_argument("--extras", type=int, nargs="+", default=[1, 1, 2], help="how many extra terms a draw may add")
    parser.add_argument("--both", action="store_true", help="also try a sawtooth across the rows")
    parser.add_argument("--min-rows", type=int, default=2)
    parser.add_argument("--list-bases", action="store_true")
    args = parser.parse_args()

    found = sorted(
        (b for b in bases(args) if len(b["ys"]) >= args.min_rows),
        key=lambda b: (-len(b["xs"]) * len(b["ys"]), -b["toothMm"]),
    )
    # One base per sawtooth and row layout: the tallest teeth that fit under the tilt limit.
    seen, chosen = set(), []
    for b in found:
        key = (tuple(sorted(abs(s) for s in b["xs"])), tuple(b["yw"]))
        if key not in seen:
            seen.add(key)
            chosen.append(b)
    if args.list_bases:
        for b in chosen:
            print(json.dumps({k: (list(map(str, v)) if k in ("xw", "yw") else v) for k, v in b.items()}))
        return

    rng = random.Random(args.seed)
    for index, b in enumerate(chosen[: args.bases]):
        num, den = terms_of(b["xw"], b["xs"], b["yw"], b["ys"])
        plain = mh.measure(mh.recipe_of(num, den), node_limit=args.node_limit)
        print(json.dumps({"base": index, "teeth": b["xs"], "rows": b["ys"], "toothMm": b["toothMm"], "extra": None, **physical(num, den), **plain}), flush=True)
        refused: dict[str, int] = {}
        for trial in range(args.trials):
            extras: dict[str, list] = {"p": [], "q": []}
            for _ in range(rng.choice(args.extras)):
                side = rng.choice("pq")
                side_terms = num if side == "p" else den
                # A term that wins in a wedge from one corner of the tray along a wall. It is close in slope
                # to the term that wins at that corner now, so the new crease is gentle; a shallow wedge
                # runs along the wall across several columns or rows, and cuts each at a different place.
                da, db = rng.choice([(i, j) for i in range(-6, 7) for j in range(-6, 7) if i and j])
                corner = (F(4) if da > 0 else F(-4), F(4) if db > 0 else F(-4))
                near = max(side_terms, key=lambda term: term.value(corner))
                reach = F(rng.randint(3, 12), 4)  # how far down the wall from the corner the crease starts, in units
                level = da * corner[0] + db * corner[1] - reach * max(abs(da), abs(db))
                extras[side].append((near.a + da, near.b + db, near.c - level))
            try:
                p, q = terms_of(b["xw"], b["xs"], b["yw"], b["ys"], extras["p"], extras["q"])
                m = physical(p, q)
            except (ValueError, ZeroDivisionError, IndexError):
                refused["no cell"] = refused.get("no cell", 0) + 1
                continue
            for name, bad in (
                ("tilt", m["maxTiltDeg"] > args.max_tilt), ("edge", m["minEdgeMm"] < args.min_edge),
                ("area", m["minAreaShare"] < args.min_area), ("angle", m["minAngleDeg"] < args.min_angle), ("congruent", bool(m["congruent"])),
            ):
                if bad:
                    refused[name] = refused.get(name, 0) + 1
            if (
                m["maxTiltDeg"] > args.max_tilt or m["minEdgeMm"] < args.min_edge or m["minAreaShare"] < args.min_area
                or m["minAngleDeg"] < args.min_angle or m["congruent"]
            ):
                continue
            try:
                out = mh.measure(mh.recipe_of(p, q), node_limit=args.node_limit)
            except (AssertionError, ValueError):
                continue
            if out["pieces"] > args.max_pieces:
                continue
            print(json.dumps({
                "base": index, "trial": trial, **m, **out,
                "terms": {"numerator": [sr.term_json(t) for t in p], "denominator": [sr.term_json(t) for t in q]},
            }), flush=True)
        print(json.dumps({"base": index, "refused": refused}), file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
