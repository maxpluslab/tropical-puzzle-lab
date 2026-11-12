# cor1 provenance

**Source.** Generated in this repository by `generator/scripts/corrugated.py --seed 3 --trials 500 --bases 4 --extras 1 2 --min-rows 4 --teeth 4 5 --steepness 2 3 4 5 6 7 8 --max-pieces 34`, base 2, trial 8. That script needs the solver from the sibling repository `maxpluslab/tiling-solvers`. There is no source archive. The exact function is stored in `recipe.json` under `source.rational`.

**Mathematics.** F = P ⊘ Q, which is P − Q classically, with P of fifteen terms and Q of four, over x, y ∈ [−4, 4]. Each piece is a two-dimensional cell of the common refinement, as in `rat1`.

**Construction.** The roof is g(x) + h(y) plus one extra term. g is a sawtooth of five faces whose two valleys stand at one height and whose two ridges stand at another, 6.1 mm apart. h is convex, in five rows of different heights. Along a valley or a ridge line the roof is h(y) plus a constant, the same on every such line, so in one row every wall on a valley line has the same height profile, and likewise on a ridge line: the roofs do not say which face stands next to which. The faces have different slopes and widths, so no two footprints are congruent. On its own this roof has 12 assemblies, since whole columns can change places. The extra term wins in a wedge along one wall, cuts each column at a different place and leaves one assembly.

**Why.** The question was whether a puzzle can be hard for a search with its roofs on, without a flat roof. Random rational puzzles are not: about 310 of them took at most 96 nodes of the contact search of tiling-solvers, around five per piece. This one takes about 1 500, with its first assembly after 1 200 to 1 400, depending on how the pieces are shuffled. It has one assembly at exact roofs and at the 1.75 mm step the player forgives. All of this is relative to the placements that search generates, in floating point.

| Limit | Required | cor1 |
| --- | --- | --- |
| Pieces | | 27 |
| Smallest piece, share of tray | ≥ 1.2% | 1.45% |
| Smallest edge | ≥ 6 mm | 12.5 mm |
| Smallest angle | ≥ 20° | 63° |
| Roof tilt, so pieces print roof-down without supports | ≤ 30° | 26.1° |
| Congruent pieces | none | none |

The limits on the two curves' lengths and on the spread of piece sizes used for `rat2` were not applied.

**Physical scale.** X = 18·x and Y = 18·y mm, giving a 144 mm square tray. Roof heights, tray rim, flat thickness and tolerances are copied from rat1.

**Status.** Exploratory puzzle. Hard for a search; how hard it is in the hand is untested.
