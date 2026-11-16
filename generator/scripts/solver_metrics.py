"""Measure every committed puzzle with the tiling-solvers search and write puzzles/solver-metrics.json.

The difficulty rating (`tropical_puzzle_lab.difficulty`) is read from that file, because the
search is in the sibling repository tiling-solvers and is not a dependency of the generator.
Run it with that repository's environment and this package on the path, after any change to
a puzzle's geometry (the rating refuses entries whose geometryHash is stale):

    cd ../tiling-solvers
    PYTHONPATH=../tropical-puzzle-lab/generator/src uv run --no-sync python \
        ../tropical-puzzle-lab/generator/scripts/solver_metrics.py

Each variant is sanitized exactly as tiling-solvers builds its corpus fixtures (same seed: pieces
turned, shuffled and renamed, no reference), searched in its own regime (relief with roofs, flat
as footprints) by `rust.contact_dfs` with no assumptions, to the end or to the node limit. The
counts are those of tiling-solvers' benchmarks/results/corpus.md. No times are recorded, so the
file is the same on every machine.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from maxplus_solvers import SolverConfig, solve
    from maxplus_solvers.io.tropical import import_puzzle, read_source
except ImportError as error:  # pragma: no cover
    raise SystemExit(f"needs maxplus_solvers from tiling-solvers on the path: {error}") from error

from tropical_puzzle_lab.export import dump  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PUZZLES = ROOT / "puzzles"
SOLVER = "rust.contact_dfs"
#: tiling-solvers' scripts/import_fixtures.py DEFAULT_SEED, so instances match its fixtures.
SEED = 20261109
#: As tiling-solvers' benchmarks/manifests/corpus.toml: well above what any finished search needs.
NODE_LIMIT = 1_500_000


def git_head(repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


def measure(path: Path, solvers: Path) -> tuple[dict, str]:
    document = read_source(path)
    # The instance records the source commit; using the fixtures' makes equal geometry hash equally.
    fixtures = json.loads((solvers / "benchmarks" / "fixtures" / "index.json").read_text(encoding="utf-8"))
    instance, _key = import_puzzle(document, seed=SEED, commit=fixtures["source"]["commit"])
    expected = {f["id"]: f["instanceHash"] for f in fixtures["fixtures"]}
    if expected.get(instance.id) not in (None, instance.instance_hash()):
        print(f"note: {instance.id} differs from the tiling-solvers fixture (geometry changed since)", file=sys.stderr)
    result = solve(instance, SolverConfig(SOLVER, mode=instance.regime, max_solutions=None, options={"node_limit": NODE_LIMIT}))
    first = solve(instance, SolverConfig(SOLVER, mode=instance.regime, max_solutions=1, options={"node_limit": NODE_LIMIT}))
    m = result.metrics
    entry = {
        "geometryHash": document["geometryHash"],
        "mode": instance.regime.value,
        "pieces": len(instance.pieces),
        "nodes": m["nodes"],
        "backtracks": m["backtracks"],
        "firstNodes": first.metrics["nodes"] if first.solutions else None,
        "solutions": len(result.solutions),
        "exhaustive": bool(result.exhaustive),
    }
    return entry, result.solver_version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ids", nargs="*", help="variant ids to measure (default: all); others are kept from the file")
    parser.add_argument("--solvers", type=Path, default=Path.cwd(), help="the tiling-solvers checkout (default: cwd)")
    args = parser.parse_args()

    out = PUZZLES / "solver-metrics.json"
    old = json.loads(out.read_text(encoding="utf-8")) if out.exists() and args.ids else {"puzzles": {}}
    entries = dict(old["puzzles"])
    version = old.get("solver", {}).get("version", "")
    for path in sorted(PUZZLES.glob("*/puzzle.json")):
        pid = path.parent.name
        if args.ids and pid not in args.ids:
            continue
        entries[pid], version = measure(path, args.solvers)
        print(json.dumps({"id": pid, **entries[pid]}), flush=True)
    document = {
        "formatVersion": 1,
        "solver": {
            "id": SOLVER, "version": version, "repository": "https://github.com/maxpluslab/tiling-solvers",
            "commit": git_head(args.solvers), "seed": SEED, "nodeLimit": NODE_LIMIT, "assumptions": [],
        },
        "puzzles": {k: entries[k] for k in sorted(entries)},
    }
    out.write_text(dump(document), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
