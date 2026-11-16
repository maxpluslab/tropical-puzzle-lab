# plt4 provenance

**Source.** Generated in this repository by `generator/scripts/lifted_search.py vertex --screen --levels 0 1 --seed 7 --node-limit 300000 --columns 4 --rows 4 --samples 600`, sample 30. That script needs the solver from the sibling repository `maxpluslab/tiling-solvers`. There is no source archive. The exact cells and roofs are stored in `recipe.json`.

**Construction.** A lifted subdivision, not a tropical one (`docs/puzzle-format.md`, Lifted recipes). The square x, y ∈ [−4, 4] is cut into a 4 × 4 grid of rectangles of unequal widths and heights, and each rectangle is cut along a diagonal, all along the same diagonal. Every grid corner is given one of two heights, and each triangle's roof is the plane through its three corners, so the roof is continuous by construction. The low level is the minimum thickness and the high level is that plus the relief.

**Why edge matching.** The solver checks roofs locally: two edges can meet when their lengths agree and the roof heights at both ends agree. With only two corner heights, every edge has one of four height profiles (low–low, low–high, high–low, high–high), so many edges of the same length look alike to the search. The pieces fit together locally in many ways, and only a nearly complete assembly shows which is right. This is the idea behind edge-matching puzzles, with heights in place of colours.

**What was tried first.** Several designs failed before this one:
- Random wedges, one per direction: few designs met the print limits, and those had several assemblies.
- Designed wedges that break a symmetric roof at one place: every candidate had one assembly, but took only about 1 300 to 1 600 nodes. The search fills the corner with the fewest candidates first, so it uses the distinctive piece early.
- Fans of triangles: pieces too thin, and 4 to 128 assemblies.
- Three heights instead of two: much easier for the search.

**Search effort.** Measured with `rust.contact_dfs` of tiling-solvers, as in `solver-metrics.json`, on the instance tiling-solvers builds (pieces turned, shuffled and renamed):

| Search | Nodes | Assemblies |
| --- | --- | --- |
| Relief, whole search | 10 787 | 1 |
| Relief, to the first assembly | 1 943 | |
| Relief, roofs matched to 1.75 mm, whole search | 11 981 | 1 |
| Relief, assuming edge to edge, whole search | 678 | 1 |
| Flat, stopped at the 1.5 million node limit | ≥ 1.5 million | ≥ 81 443 |

For comparison, cor1 takes 1 529 nodes, and every other relief puzzle takes at most 94. Assuming that pieces meet edge to edge (no vertex in the middle of another piece's edge) removes most of the effort, since it rules out the many partial matches of a long edge against a shorter one.

The player accepts roofs that meet to within 0.05 times the relief, 0.6 mm for 12 mm. One assembly at 1.75 mm is the stronger claim.

**Many flat solutions.** Without roofs, the triangles fit together in a huge number of ways. The flat search found 81 443 assemblies before it stopped at its node limit, and it was still finding more. Any of them completes the flat puzzle. Its rating of 5 measures the work of listing every assembly, not the work of finding one: the first came after 4 538 nodes.

**Print limits.** The rule against congruent footprints is relaxed for Pleat: the two halves of a rectangle are always congruent by a half turn, so pieces come in pairs, never three of a shape.

| Limit | Required | plt4 |
| --- | --- | --- |
| Pieces | | 32 |
| Smallest piece, share of tray | ≥ 1.2% | 1.48% |
| Largest piece, share of tray | ≤ 15% | 5.47% |
| Smallest edge | ≥ 6 mm | 21.0 mm |
| Smallest angle | ≥ 20° | 24.0° |
| Roof tilt, so pieces print roof-down without supports | ≤ 30° | 29.7° |
| Relief | ≥ 12 mm | 12 mm |
| Congruent footprints | pairs only | 16 pairs |

Where all four corners of a rectangle stand at one height, its two triangles have the same flat roof and are identical pieces (A3, D1, by the grid's column letter and row number). The search counts assemblies that differ only by exchanging identical pieces as one.

**Physical scale.** X = 18·x and Y = 18·y mm, giving a 144 mm square tray. Minimum thickness, tray rim, flat thickness and tolerances are copied from cor1.

**Status.** Exploratory puzzle. Hard for a search with its roofs on; how hard it is in the hand is untested. All counts are relative to the placements that search generates, in floating point.
