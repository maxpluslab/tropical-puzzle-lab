"""Measure how hard a tropical rational puzzle is for a search, with its roofs on.

Exploration. Needs `maxplus_solvers` from the sibling repository tiling-solvers, so run it
with that repository's environment and this package on the path:

    cd ../tiling-solvers
    PYTHONPATH=../tropical-puzzle-lab/generator/src uv run --no-sync python \
        ../tropical-puzzle-lab/generator/scripts/measure_hardness.py corpus
    ... measure_hardness.py sample --seed 1 --samples 20000
    ... measure_hardness.py climb --seed 1 --restarts 4 --evals 400

A candidate is a pair of term lists (P, Q). It is built into the relief puzzle document the
exporter would write, sanitized by tiling-solvers (pieces turned, shuffled and renamed, so
the search gets no hint), and searched to the end. What comes back:

- `nodes`: nodes of the whole search, the cost of finding every assembly and showing there
  is no other, relative to the placements the search generates;
- `first`: nodes to the first assembly;
- `solutions`: assemblies found, up to turning the tray;
- `degree`: mean number of edges of other pieces each piece edge could lie against with
  continuous roofs (the edge compatibility graph of tiling-solvers);
- the same at the player's roof tolerance instead of exact roofs (`nodesLoose`, ...).

Every candidate has the corpus's physical scale: a 144 mm tray and 35 mm of relief. The
relief is fixed, so nothing here gets harder by getting flatter overall.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import search_rational as sr  # noqa: E402
from tropical_puzzle_lab.export import Construction, build_puzzle  # noqa: E402
from tropical_puzzle_lab.tropical import Term  # noqa: E402

try:
    from maxplus_solvers import SolverConfig, solve
    from maxplus_solvers.experiments import proxies
    from maxplus_solvers.io.tropical import import_puzzle
    from maxplus_solvers.models import Regime
except ImportError as error:  # pragma: no cover
    raise SystemExit(f"needs maxplus_solvers from tiling-solvers on the path: {error}") from error

VALIDATION = {
    "contactNoise": 1e-06, "overlapDepth": 0.006, "outsideDepth": 0.006, "areaError": 0.012,
    "roofMismatch": 0.05, "edgeAngleDeg": 3, "edgeMinOverlap": 0.02,
}
PLAYER_ROOF_MM = 1.75
SOLVER = "rust.contact_dfs"


def recipe_of(numerator: list[Term], denominator: list[Term], name: str = "candidate") -> dict:
    return {
        "formatVersion": 1, "family": "tropical-rational", "convention": "max", "id": name, "revision": 1,
        "domain": str(sr.DOMAIN), "xyMmPerUnit": str(sr.XY), "minThicknessMm": str(sr.MIN_THICKNESS),
        "reliefMm": str(sr.RELIEF), "trayRimMm": "7",
        "numerator": [sr.term_json(t) for t in numerator], "denominator": [sr.term_json(t) for t in denominator],
        "validation": VALIDATION, "scramble": {"algorithm": "v1", "defaultSeed": 1}, "source": {},
    }


def relief_document(recipe: dict) -> dict:
    construction = Construction(recipe)
    construction.check()
    variant = {"id": recipe["id"], "variant": "relief", "name": recipe["id"], "description": "", "notes": []}
    return build_puzzle(recipe, variant, construction)


def search(instance, *, first: bool, node_limit: int, roof_mm: float | None, mode=None):
    options = {"node_limit": node_limit}
    if roof_mm is not None:
        options["roof_tolerance_mm"] = roof_mm
    config = SolverConfig(SOLVER, mode=mode or instance.regime, max_solutions=1 if first else None, options=options)
    return solve(instance, config)


def measure(recipe: dict, *, node_limit: int = 200_000, seed: int = 1, flat: bool = False) -> dict:
    """Search one candidate. `flat` adds the footprint search of the same pieces, for scale."""
    instance, _key = import_puzzle(relief_document(recipe), seed=seed, commit="exploration")
    out: dict = {"pieces": len(instance.pieces)}
    exact = search(instance, first=False, node_limit=node_limit, roof_mm=None)
    out.update(
        nodes=exact.metrics["nodes"], whole=exact.exhaustive, solutions=len(exact.solutions),
        deadEndDepth=round(exact.metrics["backtrack_depth"] / max(1, exact.metrics["backtracks"]), 2),
        first=search(instance, first=True, node_limit=node_limit, roof_mm=None).metrics["nodes"],
        degree=round(proxies.static(instance).mean_degree, 2),
    )
    loose = search(instance, first=False, node_limit=node_limit, roof_mm=PLAYER_ROOF_MM)
    out.update(nodesLoose=loose.metrics["nodes"], wholeLoose=loose.exhaustive, solutionsLoose=len(loose.solutions))
    if flat:
        bare = search(instance, first=False, node_limit=node_limit, roof_mm=None, mode=Regime.FOOTPRINT)
        out.update(nodesFlat=bare.metrics["nodes"], wholeFlat=bare.exhaustive, solutionsFlat=len(bare.solutions))
    return out


def terms_from(items: list[dict]) -> list[Term]:
    return [Term(t["id"], int(t["a"]), int(t["b"]), Fraction(t["c"])) for t in items]


def run_corpus(args: argparse.Namespace) -> None:
    """The committed rational puzzles, as a check that this route gives the costs tiling-solvers reports."""
    for path in sorted((Path(__file__).resolve().parents[2] / "puzzles").glob("*/recipe.json")):
        recipe = json.loads(path.read_text(encoding="utf-8"))
        print(json.dumps({"id": recipe["id"], **measure(recipe, node_limit=args.node_limit, flat=args.flat)}), flush=True)


def draw_on_grid(rng: random.Random, count: int, letters: str, grid: int) -> list[Term]:
    """Like the sampler's `draw_terms`, with coefficients on a grid of 1/`grid` over the same range of -4 to 4.

    A coarse grid puts the vertices of the cells on a lattice and the roof heights at them on
    a few levels, so that many corners of different pieces stand at the same height.
    """
    terms = [Term("", a, b, Fraction(rng.randint(-4 * grid, 4 * grid), grid)) for a, b in rng.sample(sr.SLOPES, count)]
    active = []
    for t in terms:
        cell = sr.square(sr.DOMAIN)
        for u in terms:
            if u is not t:
                cell = sr.clip(cell, (t.a - u.a, t.b - u.b), u.c - t.c)
        if sr.area(cell) > 0:
            active.append(t)
    return [Term(letters[i], t.a, t.b, t.c) for i, t in enumerate(active)]


def height_levels(recipe: dict) -> tuple[int, int]:
    """(distinct roof heights at piece vertices to 0.01 mm, piece vertices): few levels for many vertices is a terraced roof."""
    c = Construction(recipe)
    heights = [round(float(c.height(t, v)), 2) for t, piece in zip(c.terms, c.pieces) for v in piece]
    return len(set(heights)), len(heights)


def run_sample(args: argparse.Namespace) -> None:
    """Random candidates that pass the sampler's physical limits: the baseline."""
    rng = random.Random(args.seed)
    if args.allow_congruent:
        # The sampler refuses congruent footprints. With different roofs they are different pieces, and decoys.
        sr.signature = lambda poly: id(poly)
    for sample in range(args.samples):
        numerator = draw_on_grid(rng, rng.randint(3, 6), "ABCDEF", args.grid)
        denominator = draw_on_grid(rng, rng.randint(3, 6), "abcdef", args.grid)
        if sr.evaluate(numerator, denominator) is None:
            continue
        row = {"sample": sample, **measure(recipe_of(numerator, denominator), node_limit=args.node_limit, flat=args.flat)}
        row["wallAmbiguity"] = round(sr.hardness(numerator, denominator)["wallAmbiguity"], 2)
        row["levels"], row["vertices"] = height_levels(recipe_of(numerator, denominator))
        row["terms"] = {"numerator": [sr.term_json(t) for t in numerator], "denominator": [sr.term_json(t) for t in denominator]}
        print(json.dumps(row), flush=True)


def run_climb(args: argparse.Namespace) -> None:
    """Hill-climb on the search cost itself: first to meet the physical limits, then to raise `--objective`."""
    rng = random.Random(args.seed)
    letters = "ABCDEFGHIJ"
    for restart in range(args.restarts):
        numerator = sr.draw_climb_terms(rng, args.terms, letters)
        denominator = sr.draw_climb_terms(rng, args.terms, letters.lower())
        best = None
        for step in range(args.evals):
            if best and rng.random() < 0.5:
                p, q = sr.mutate(rng, numerator), denominator
            else:
                p, q = numerator, (sr.mutate(rng, denominator) if best else denominator)
            try:
                m = sr.climb_metrics(p, q)
            except (ValueError, ZeroDivisionError):
                continue
            miss = sr.shortfall(m, args)
            found = None
            if miss == 0:
                try:
                    found = measure(recipe_of(p, q), node_limit=args.node_limit)
                except (AssertionError, ValueError):
                    continue
            score = (1, found[args.objective]) if found else (0, -miss)
            if best is None or score >= best[0]:
                if found and (best is None or score > best[0]):
                    print(json.dumps({"restart": restart, "step": step, **found}), flush=True)
                best = (score, m, found)
                numerator, denominator = p, q
        if best and best[2]:
            print(json.dumps({
                "restart": restart, "final": True, **best[2],
                "heightIqrMm": round(best[1]["heightIqrMm"], 1), "maxTiltDeg": round(best[1]["maxTiltDeg"], 1),
                "wallAmbiguity": round(sr.hardness(numerator, denominator)["wallAmbiguity"], 2),
                "terms": {"numerator": [sr.term_json(t) for t in numerator], "denominator": [sr.term_json(t) for t in denominator]},
            }), flush=True)
        else:
            print(json.dumps({"restart": restart, "final": True, "met": False}), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("corpus", "sample", "climb"):
        sub = commands.add_parser(name)
        sub.add_argument("--seed", type=int, default=1)
        sub.add_argument("--node-limit", type=int, default=200_000)
        sub.add_argument("--flat", action="store_true", help="also search the footprints without roofs")
        if name == "sample":
            sub.add_argument("--samples", type=int, default=20000)
            sub.add_argument("--grid", type=int, default=20, help="coefficients are multiples of 1/GRID")
            sub.add_argument("--allow-congruent", action="store_true", help="keep candidates with congruent footprints")
        if name == "climb":
            sub.add_argument("--restarts", type=int, default=4)
            sub.add_argument("--evals", type=int, default=400)
            sub.add_argument("--objective", default="nodes", choices=["nodes", "first", "degree", "nodesLoose"])
            sub.add_argument("--terms", type=int, default=5)
            sub.add_argument("--min-pieces", type=int, default=12)
            sub.add_argument("--max-pieces", type=int, default=20)
            sub.add_argument("--min-area", type=float, default=0.012)
            sub.add_argument("--max-area", type=float, default=0.2)
            sub.add_argument("--min-height-iqr", type=float, default=10.0)
            sub.add_argument("--min-edge", type=float, default=6.0)
            sub.add_argument("--min-angle", type=float, default=20.0)
            sub.add_argument("--max-tilt", type=float, default=30.0)
            sub.add_argument("--min-balance", type=float, default=0.4)
    args = parser.parse_args()
    {"corpus": run_corpus, "sample": run_sample, "climb": run_climb}[args.command](args)


if __name__ == "__main__":
    main()
