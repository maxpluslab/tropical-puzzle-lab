"""The lifting space of a subdivision, on examples worked out by hand.

Dimensions follow from Maxwell–Cremona: 3 (the affine roofs) plus one per
independent self-stress of the interior edges. Generically a stress space has
dimension E - 2V over interior edges E and interior vertices V, since each
interior vertex must be in equilibrium in two directions.
"""
from fractions import Fraction as F
from pathlib import Path

import pytest

from tropical_puzzle_lab.export import Construction, load_recipe
from tropical_puzzle_lab.geometry import square
from tropical_puzzle_lab.lifting import (
    IDENTITY,
    continuity_rows,
    creases,
    edge_to_edge,
    lifting_space,
    quarter_turn,
    rival_space,
    satisfies,
    seams,
    stress_of,
    tiles,
    translation,
)

PUZZLES = Path(__file__).resolve().parents[2] / "puzzles"


def rect(x0, y0, x1, y1):
    x0, y0, x1, y1 = F(x0), F(y0), F(x1), F(y1)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def poly(*points):
    return [(F(x), F(y)) for x, y in points]


HALVES = [rect(-1, -1, 0, 1), rect(0, -1, 1, 1)]
CROSS = [rect(-1, -1, 0, 0), rect(0, -1, 1, 0), rect(0, 0, 1, 1), rect(-1, 0, 0, 1)]
# One interior vertex at the origin, joined to the top midpoint and the two bottom corners.
Y = [
    poly((0, 0), (0, 1), (-1, 1), (-1, -1)),
    poly((0, 0), (-1, -1), (1, -1)),
    poly((0, 0), (1, -1), (1, 1), (0, 1)),
]
# Four 2x1 rectangles round a unit square, in a 3x3 tray.
PINWHEEL = [rect(0, 0, 2, 1), rect(2, 0, 3, 2), rect(1, 2, 3, 3), rect(0, 1, 1, 3), rect(1, 1, 2, 2)]


def test_one_cell_lifts_only_to_planes():
    assert len(lifting_space([square(F(1))])) == 3


def test_a_line_cut_carries_one_stress():
    """E = 1 interior edge, V = 0 interior vertices: 3 + 1."""
    space = lifting_space(HALVES)
    assert len(space) == 4
    bent = [v for v in space if creases(HALVES, v)]
    assert bent and all(len(creases(HALVES, v)) == 1 for v in bent)


def test_a_cross_carries_a_stress_on_each_line():
    """E = 4 half-lines, V = 1: 4 - 2 = 2 stresses, the folds along x = 0 and y = 0."""
    assert len(lifting_space(CROSS)) == 5


def test_a_three_way_vertex_carries_one_stress():
    """E = 3, V = 1: 3 - 2 = 1, the tropical Y."""
    assert len(lifting_space(Y)) == 4


def test_the_pinwheel_lifts_only_to_planes():
    """The classic subdivision with no lifting but the flat ones.

    Each corner of the centre square is a T: two collinear edges and a third.
    Equilibrium there needs the third edge's weight to be zero and the two
    collinear weights equal; going round the square, every weight is zero.
    E = 8, V = 4: 8 - 2*4 = 0.
    """
    assert tiles(PINWHEEL, rect(0, 0, 3, 3))
    assert len(lifting_space(PINWHEEL)) == 3


def test_every_lifting_is_continuous_and_bends_only_normal_to_its_seams():
    for cells in (HALVES, CROSS, Y, PINWHEEL):
        rows = continuity_rows(cells)
        for v in lifting_space(cells):
            assert satisfies(rows, v)
            stress_of(cells, v)  # raises on a tangential jump


def test_a_jump_along_a_seam_is_refused():
    # Left half with gradient (0, 1), right half with gradient (0, 0): the jump runs along x = 0.
    v = [F(0), F(1), F(0), F(0), F(0), F(0)]
    with pytest.raises(ValueError, match="not normal"):
        stress_of(HALVES, v)


def test_the_fold_has_unit_stress():
    """|x| on the halves: gradients (-1, 0) and (1, 0).

    The left cell's edge on x = 0 runs from (0, -1) to (0, 1), d = (0, 2), n = (-2, 0);
    the jump is (-1, 0) - (1, 0) = (-2, 0), so w = (-2, 0).(-2, 0) / 4 = 1.
    """
    v = [F(-1), F(0), F(0), F(1), F(0), F(0)]
    (w,) = stress_of(HALVES, v).values()
    assert w == 1


def test_t_junctions_are_found():
    assert edge_to_edge(HALVES) and edge_to_edge(CROSS) and edge_to_edge(Y)
    assert not edge_to_edge(PINWHEEL)
    # A cell edge that only partly meets a longer one is still a seam: the pinwheel has
    # four spokes and the four sides of the centre square.
    assert len(seams(PINWHEEL)) == 8


def test_swapping_the_halves_asks_for_a_roof_symmetric_about_the_cut():
    """F = c + a*x + b*y + l*|x| on the halves; swap them (left moves by +1, right by -1).

    Left roof c + (a - l)x + by, right c + (a + l)x + by. In the swap the left
    cell's x = -1 wall meets the right cell's x = 1 wall at the new seam x = 0:
    c - a + l + by = c + a + l + by, so a = 0. The rival leaves c, b and l: 3.
    """
    swap = [translation(1, 0), translation(-1, 0)]
    assert tiles([[m.apply(p) for p in c] for c, m in zip(HALVES, swap)], square(F(1)))
    space = rival_space(HALVES, [swap])
    assert len(space) == 3
    # a = (a_left + a_right) / 2 is zero on all of it.
    assert all(v[0] + v[3] == 0 for v in space)


def test_a_breaker_seam_frees_the_rival():
    swap = [translation(1, 0), translation(-1, 0)]
    moved = [[m.apply(p) for p in c] for c, m in zip(HALVES, swap)]
    (seam,) = seams(moved)
    assert len(rival_space(HALVES, [swap], exempt=[(0, seam)])) == 4


def test_a_quarter_turn_of_the_tray_is_a_rival_of_the_cross():
    """Turning every quadrant about the centre maps the cross onto itself.

    A roof continuous in that rival as in the original is any roof, since the
    turned assembly is the same assembly seen from another side: 5 again.
    """
    turn = [quarter_turn(1)] * 4
    assert tiles([[m.apply(p) for p in c] for c, m in zip(CROSS, turn)], square(F(1)))
    assert len(rival_space(CROSS, [turn])) == 5
    assert len(rival_space(CROSS, [[IDENTITY] * 4])) == 5


def test_a_tropical_roof_is_a_lifting():
    """cor1's cells and affine pieces satisfy every continuity equation."""
    c = Construction(load_recipe(PUZZLES / "cor1" / "recipe.json"))
    v = [x for t in c.terms for x in (F(t.a), F(t.b), t.c)]
    assert satisfies(continuity_rows(c.cells), v)
    assert edge_to_edge(c.cells)
