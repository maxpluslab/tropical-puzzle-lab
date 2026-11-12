import math
from fractions import Fraction
from pathlib import Path

import pytest

from tropical_puzzle_lab.export import Construction, build_puzzle, dump, load_recipe, terms_of
from tropical_puzzle_lab.geometry import area, centroid
from tropical_puzzle_lab.tropical import Term, refine, regions, tropical_value

PUZZLES = Path(__file__).resolve().parents[2] / "puzzles"
RECIPES = ["rat1", "rat2", "cor1"]


@pytest.fixture(scope="module", params=RECIPES)
def recipe(request):
    return load_recipe(PUZZLES / request.param / "recipe.json")


@pytest.fixture(scope="module")
def construction(recipe):
    return Construction(recipe)


def to_domain(c, v):
    return (v[0] / c.xy + c.center[0], v[1] / c.xy + c.center[1])


def test_reference_assembly_is_valid(construction):
    construction.check()


def test_each_cell_is_where_its_two_terms_win(recipe, construction):
    numerator, denominator = terms_of(recipe, "numerator"), terms_of(recipe, "denominator")
    by_id = {t.id: t for t in numerator + denominator}
    for term, cell in zip(construction.terms, construction.cells):
        p, q = by_id[term.id[0]], by_id[term.id[1]]
        m = centroid(cell)
        assert all(p.value(m) > t.value(m) for t in numerator if t is not p)
        assert all(q.value(m) > t.value(m) for t in denominator if t is not q)
        assert (term.a, term.b, term.c) == (p.a - q.a, p.b - q.b, p.c - q.c)


def test_roof_is_graph_of_difference(recipe, construction):
    numerator, denominator = terms_of(recipe, "numerator"), terms_of(recipe, "denominator")
    r = construction.roof
    for term, piece in zip(construction.terms, construction.pieces):
        for v in piece:
            point = to_domain(construction, v)
            f = tropical_value(numerator, point) - tropical_value(denominator, point)
            assert construction.height(term, v) == r.min_thickness + r.scale * (f - r.f_min)


def test_roof_has_valleys_and_ridges(construction):
    # Across a shared edge the roof folds up (valley: F is the max of the two planes there) or down
    # (ridge: the min). Unlike a tropical polynomial, a rational function has both.
    kinds = set()
    c = construction
    for i, (ti, p) in enumerate(zip(c.terms, c.pieces)):
        for tj, q in zip(c.terms[i + 1:], c.pieces[i + 1:]):
            shared = set(p) & set(q)
            if len(shared) < 2 or (ti.a, ti.b) == (tj.a, tj.b):
                continue
            # Compare the two planes just inside piece i, at its centroid.
            m = to_domain(c, centroid(p))
            kinds.add("valley" if ti.value(m) > tj.value(m) else "ridge")
    assert kinds == {"valley", "ridge"}


def test_refine_with_one_denominator_term_is_the_polynomial():
    numerator = [Term("A", 0, 0, Fraction(0)), Term("B", 1, 0, Fraction(-1)), Term("C", 0, 1, Fraction(1, 2))]
    q = Term("a", 1, 1, Fraction(3))
    terms, cells = refine(numerator, [q], Fraction(3))
    assert cells == regions(numerator, Fraction(3))
    assert [(t.id, t.a, t.b, t.c) for t in terms] == [(p.id + "a", p.a - 1, p.b - 1, p.c - 3) for p in numerator]


def test_cells_tile_the_domain(construction):
    assert sum(area(cell) for cell in construction.cells) == (2 * construction.domain) ** 2


@pytest.mark.parametrize(("name", "fewest", "most"), [("rat2", 20, 24), ("cor1", 27, 27)])
def test_the_larger_puzzles_meet_their_print_limits(name, fewest, most):
    c = Construction(load_recipe(PUZZLES / name / "recipe.json"))
    tray = float(2 * c.domain * c.xy) ** 2
    polygons = [[(float(x), float(y)) for x, y in piece] for piece in c.pieces]
    assert fewest <= len(polygons) <= most
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


def test_cor1_is_corrugated():
    """Its valleys stand at one height and its ridges at another.

    The sawtooth's lines are the creases that meet the top wall, which the wedge does not reach
    (it runs along the bottom wall). Valleys and ridges alternate
    along it, and the roof is as high at one valley as at the next, and at one ridge as at the next:
    that is what makes the walls on those lines look alike.
    """
    recipe = load_recipe(PUZZLES / "cor1" / "recipe.json")
    c = Construction(recipe)
    numerator, denominator = terms_of(recipe, "numerator"), terms_of(recipe, "denominator")
    top = c.domain
    lines = sorted({v[0] for cell in c.cells for v in cell if v[1] == top and abs(v[0]) < c.domain})
    assert len(lines) == 4
    floor = [tropical_value(numerator, (x, top)) - tropical_value(denominator, (x, top)) for x in lines]
    assert floor[0] == floor[2] and floor[1] == floor[3]
    # In mm: well clear of the 1.75 mm step the player forgives.
    assert float(c.roof.scale * abs(floor[0] - floor[1])) > 6.0


def test_committed_puzzles_are_current(recipe, construction):
    for variant in recipe["variants"]:
        puzzle = build_puzzle(recipe, variant, construction)
        assert "terms" not in puzzle["tropical"] and puzzle["tropical"]["numerator"] == recipe["numerator"]
        committed = (PUZZLES / variant["id"] / "puzzle.json").read_text(encoding="utf-8")
        assert committed == dump(puzzle), f"run tpl-export to regenerate {variant['id']}"
