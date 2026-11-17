"""The Pleat puzzles: lifted recipes on a grid of rectangles, each cut along a diagonal.

Every grid corner stands at one of two heights, so the same edge profiles recur across the
tray (provenance.md of each puzzle). These tests check the recipes against that design and
against the print limits, which for Pleat allow pairs of congruent pieces: the two halves of
a rectangle are always congruent by a half turn.
"""
import math
from collections import Counter
from pathlib import Path

import pytest

from tropical_puzzle_lab.export import Construction, build_puzzle, dump, load_recipe
from tropical_puzzle_lab.geometry import area
from tropical_puzzle_lab.lifting import edge_to_edge
from tropical_puzzle_lab.naming import construction_name

PUZZLES = Path(__file__).resolve().parents[2] / "puzzles"
# id -> (name, columns, rows): the name by the naming rules, the grid by design.
PLEATS = {
    "plt1": ("Pleat 32a", 4, 4),
    "plt2": ("Pleat 32b", 4, 4),
    "plt3": ("Pleat 32c", 4, 4),
    "plt4": ("Pleat 32d", 4, 4),
    "plt5": ("Pleat 24e", 4, 3),
}


@pytest.fixture(scope="module", params=list(PLEATS))
def pleat(request):
    recipe = load_recipe(PUZZLES / request.param / "recipe.json")
    return request.param, recipe, Construction(recipe)


def test_reference_assembly_is_valid(pleat):
    _, _, c = pleat
    c.check()


def test_name_and_piece_count(pleat):
    pid, recipe, c = pleat
    name, columns, rows = PLEATS[pid]
    # Two triangles per rectangle of the grid.
    assert len(c.pieces) == 2 * columns * rows
    assert construction_name(recipe, len(c.pieces)) == name


def test_cells_are_triangles_that_tile_the_domain(pleat):
    _, _, c = pleat
    assert all(len(cell) == 3 for cell in c.cells)
    assert sum(area(cell) for cell in c.cells) == (2 * c.domain) ** 2


def test_every_corner_stands_at_one_of_two_heights(pleat):
    """The design: two roof levels at the grid corners, nothing in between."""
    _, _, c = pleat
    heights = {c.height(t, v) for t, piece in zip(c.terms, c.pieces) for v in piece}
    assert len(heights) == 2
    # The lower level is the minimum thickness and the upper is that plus the relief.
    assert heights == {c.roof.min_thickness, c.roof.min_thickness + c.roof.relief}


def test_no_vertex_lies_inside_another_edge(pleat):
    _, _, c = pleat
    assert edge_to_edge(c.cells)


def shape(poly):
    """A footprint up to rotation: its cyclic sequence of edge lengths and angles, rounded."""
    n = len(poly)
    steps = []
    for k in range(n):
        a, b, d = poly[k - 1], poly[k], poly[(k + 1) % n]
        u, v = (a[0] - b[0], a[1] - b[1]), (d[0] - b[0], d[1] - b[1])
        angle = math.atan2(abs(u[0] * v[1] - u[1] * v[0]), u[0] * v[0] + u[1] * v[1])
        steps.append((round(math.dist(b, d), 6), round(angle, 6)))
    return min(tuple(steps[k:] + steps[:k]) for k in range(n))


def test_print_limits_with_twin_pairs(pleat):
    _, _, c = pleat
    tray = float(2 * c.domain * c.xy) ** 2
    polygons = [[(float(x), float(y)) for x, y in piece] for piece in c.pieces]
    areas = [float(area(piece)) / tray for piece in c.pieces]
    assert min(areas) >= 0.012 and max(areas) <= 0.15
    for poly in polygons:
        n = len(poly)
        for k in range(n):
            a, b, d = poly[k - 1], poly[k], poly[(k + 1) % n]
            assert math.dist(b, d) >= 6
            u, v = (a[0] - b[0], a[1] - b[1]), (d[0] - b[0], d[1] - b[1])
            angle = math.atan2(abs(u[0] * v[1] - u[1] * v[0]), u[0] * v[0] + u[1] * v[1])
            assert math.degrees(angle) >= 20
    tilts = [math.degrees(math.atan(float(c.roof.scale) * math.hypot(t.a, t.b) / float(c.xy))) for t in c.terms]
    assert max(tilts) <= 30
    assert float(c.roof.relief) >= 12
    # Twins come in pairs, never three of a shape.
    assert max(Counter(shape(p) for p in polygons).values()) == 2


def test_shape_tells_a_half_turn_from_a_different_triangle():
    # A right triangle and its half turn are one shape; its mirror image (a flip) is not
    # necessarily, but a different triangle always is a different shape.
    t = [(0.0, 0.0), (3.0, 0.0), (0.0, 4.0)]
    turned = [(-x, -y) for x, y in t]
    other = [(0.0, 0.0), (3.0, 0.0), (0.0, 5.0)]
    assert shape(t) == shape(turned)
    assert shape(t) != shape(other)


def test_committed_puzzles_are_current(pleat):
    _, recipe, c = pleat
    for variant in recipe["variants"]:
        puzzle = build_puzzle(recipe, variant, c)
        assert "tropical" not in puzzle and puzzle["lifting"]["cells"] == recipe["cells"]
        committed = (PUZZLES / variant["id"] / "puzzle.json").read_text(encoding="utf-8")
        assert committed == dump(puzzle), f"run tpl-export to regenerate {variant['id']}"
