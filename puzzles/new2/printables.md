# Printables listing: Hill 16b-r (`new2`)

Published: https://www.printables.com/model/1914257-tropical-puzzle-hill-16b-r-16-piece-relief-tiling

Relief variant only; the flat variant (Hill 16b-f) is not listed yet. Conventions and template: [docs/printables.md](../../docs/printables.md).

**Name:** Tropical Puzzle Hill 16b-r: 16-piece relief tiling puzzle

**Summary:** 16-piece tropical puzzle where sloped tops form one hill. Play: https://maxpluslab.github.io/tropical-puzzle-lab/

**Tags:** puzzle, tiling puzzle, jigsaw, brain teaser, tray puzzle, mathematical puzzle, math, tropical geometry

**Description:**

Hill 16b-r is a 3D-printable puzzle from [Tropical Puzzle Lab](https://maxpluslab.github.io/tropical-puzzle-lab/), a project of [MaxPlusLab](https://github.com/maxpluslab) that builds puzzles from tropical geometry. There are 16 convex pieces, 16 to 43 mm tall, each with a sloped flat top, and a 144 mm square tray.

The puzzle is solved when two things are true:
1. the pieces fill the tray with no gaps, and
2. every pair of neighbouring pieces meets at the same height along their shared edge, so the tops form one unbroken roof that rises to ridges.

Many outlines look alike, and the heights along each edge are your best clue. In the online version it has the highest difficulty rating (5 of 5).

**The mathematics.** The roof is the graph of the min-convention tropical polynomial F(x, y) = min over (a, b) ∈ {1,…,4}² of (cₐᵦ + a·x + b·y), the smallest of 16 planes. Each piece is the region where one plane is the lowest. Because F is a minimum of planes, it is concave, so the finished roof is a faceted hill. The lines between pieces form a tropical curve.

**Play online:** https://maxpluslab.github.io/tropical-puzzle-lab/ (this puzzle: https://maxpluslab.github.io/tropical-puzzle-lab/?puzzle=new2; the online version also has a flat mode, where the heights are removed) · How it works: https://maxpluslab.github.io/tropical-puzzle-lab/?page=math

**Files:** `tray.stl` (152 × 152 × 10 mm, 144 mm cavity) and `piece-A.stl` … `piece-P.stl`.

**Printing.** Tested on a Prusa MK3S+ with these settings:
- PLA, 0.4 mm nozzle
- 0.20 mm layers (PrusaSlicer "QUALITY" profile)
- 15% gyroid infill
- All 16 pieces in one print: load them together and use PrusaSlicer's **Arrange** (A) to fit them on the plate
- The tray as a separate print

**Notes:**
- Import at 100%. The units are mm.
- The pieces are oriented **roof-down**: the sloped top lies on the bed, so it comes out smooth. The walls overhang by at most 15.7°, so you don't need supports.
- PrusaSlicer may warn that the tall, narrow pieces could be unstable. On the MK3S+ it was safe to ignore, and none of the pieces came loose.
- Each piece edge is inset by 0.15 mm, which leaves about 0.3 mm between neighbours and 0.15 mm at the tray wall. Keep elephant's-foot compensation on.

**Tip:** start with the steepest pieces. They belong at the high edges of the hill.

More from [MaxPlusLab](https://github.com/maxpluslab) · Source and generator (MIT): https://github.com/maxpluslab/tropical-puzzle-lab
