# Printables listing: Terrain 20a-r (`rat2`)

Published: https://www.printables.com/model/1914271-tropical-puzzle-terrain-20a-r-20-piece-relief-tili

Relief variant only; the flat variant (Terrain 20a-f) is not listed. Conventions and template: [docs/printables.md](../../docs/printables.md).

**Name:** Tropical Puzzle Terrain 20a-r: 20-piece relief tiling puzzle

**Summary:** 20-piece tropical puzzle: a roof of peaks, pits and saddles. Play: https://maxpluslab.github.io/tropical-puzzle-lab/

**Tags:** puzzle, tiling puzzle, jigsaw, brain teaser, tray puzzle, mathematical puzzle, math, tropical geometry

**Description:**

Terrain 20a-r is a 3D-printable puzzle from [Tropical Puzzle Lab](https://maxpluslab.github.io/tropical-puzzle-lab/), a project of [MaxPlusLab](https://github.com/maxpluslab) that builds puzzles from tropical geometry. There are 20 convex pieces, each with a sloped flat top, and a 144 mm square tray. The pieces are 8 to 43 mm thick.

The puzzle is solved when two things are true:
1. the pieces fill the tray with no gaps, and
2. every pair of neighbouring pieces meets at the same height along their shared edge, so the tops form one unbroken landscape with three peaks, two pits and three saddles.

Unlike a hill or a bowl, the roof both rises and falls, so you can't sort the pieces simply by height. In the online version it has the highest difficulty rating (5 of 5).

**The mathematics.** The roof is the graph of a tropical rational function F = P ⊘ Q, which is P − Q in ordinary arithmetic. P and Q are each the largest of seven planes. Each piece is a region where one plane of P and one plane of Q are both the largest, so its top is the difference of those two planes. P's tropical curve turns into the valleys of the roof and Q's into the ridges; where they cross, you get peaks, pits and saddles.

**Play online:** https://maxpluslab.github.io/tropical-puzzle-lab/ (this puzzle: https://maxpluslab.github.io/tropical-puzzle-lab/?puzzle=rat2; the online version also has a flat mode, where the heights are removed) · How it works: https://maxpluslab.github.io/tropical-puzzle-lab/?page=math

**Files:** `tray.stl` (152 × 152 × 10 mm, 144 mm cavity) and 20 pieces, `piece-Ac.stl` … `piece-Gg.stl`. Each piece's name pairs a plane of P (capital letter) with a plane of Q (small letter).

**Printing.** Tested on a Prusa MK3S+ with these settings:
- PLA, 0.4 mm nozzle
- 0.20 mm layers (PrusaSlicer "QUALITY" profile)
- 15% gyroid infill
- All 20 pieces in one print: load them together and use PrusaSlicer's **Arrange** (A) to fit them on the plate
- The tray as a separate print

**Notes:**
- Import at 100%. The units are mm.
- The pieces are oriented **roof-down**: the sloped top lies on the bed, so it comes out smooth. The walls overhang by at most 28°, so you don't need supports.
- PrusaSlicer may warn that the tall, narrow pieces could be unstable. On the MK3S+ it was safe to ignore, and none of the pieces came loose.
- Each piece edge is inset by 0.15 mm, which leaves about 0.3 mm between neighbours and 0.15 mm at the tray wall. Keep elephant's-foot compensation on.

**Tip:** around a peak every top slopes away, and around a pit every top slopes in. Find those pieces first.

More from [MaxPlusLab](https://github.com/maxpluslab) · Source and generator (MIT): https://github.com/maxpluslab/tropical-puzzle-lab
