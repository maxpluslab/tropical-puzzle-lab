# Printables listing: Corrugated 27a-r (`cor1`)

Published: https://www.printables.com/model/1914628-tropical-puzzle-corrugated-27a-r-27-piece-relief-t

Relief variant only; the flat variant (Corrugated 27a-f) is not listed. Conventions and template: [docs/printables.md](../../docs/printables.md).

**Name:** Tropical Puzzle Corrugated 27a-r: 27-piece relief tiling puzzle

**Summary:** 27-piece tropical puzzle: a roof of look-alike ridges. Play: https://maxpluslab.github.io/tropical-puzzle-lab/

**Tags:** puzzle, tiling puzzle, jigsaw, brain teaser, tray puzzle, mathematical puzzle, math, tropical geometry

**Description:**

Corrugated 27a-r is a 3D-printable puzzle from [Tropical Puzzle Lab](https://maxpluslab.github.io/tropical-puzzle-lab/), a project of [MaxPlusLab](https://github.com/maxpluslab) that builds puzzles from tropical geometry. There are 27 convex pieces, each with a sloped flat top, and a 144 mm square tray. The pieces are 8 to 43 mm thick.

The puzzle is solved when two things are true:
1. the pieces fill the tray with no gaps, and
2. every pair of neighbouring pieces meets at the same height along their shared edge, so the tops form one unbroken corrugated roof of ridges and valleys.

In most relief puzzles the heights tell you which pieces belong together. This one was designed so that they help as little as possible: every valley line has the same height profile, and so does every ridge line, so many edges match many others. No two pieces have the same outline, and a computer search finds only one solution. It is our largest puzzle and has the highest difficulty rating online (5 of 5).

**The mathematics.** The roof is the graph of a tropical rational function F = P ⊘ Q, which is P − Q in ordinary arithmetic. P is the largest of fifteen planes and Q the largest of four. Each piece is a region where one plane of P and one plane of Q are both the largest, so its top is the difference of those two planes. P's tropical curve turns into the valleys of the roof and Q's into the ridges. The mathematics page explains how the corrugation is built, with the figures that give the solution away kept behind a cover.

**Play online:** https://maxpluslab.github.io/tropical-puzzle-lab/ (this puzzle: https://maxpluslab.github.io/tropical-puzzle-lab/?puzzle=cor1; the online version also has a flat mode, where the heights are removed) · How it works: https://maxpluslab.github.io/tropical-puzzle-lab/?page=math

**Files:** `tray.stl` (152 × 152 × 10 mm, 144 mm cavity) and 27 pieces, `piece-Aa.stl` … `piece-Oc.stl`. Each piece's name pairs a plane of P (capital letter) with a plane of Q (small letter).

**Printing.** Tested on a Prusa MK3S+ with these settings:
- PLA, 0.4 mm nozzle
- 0.20 mm layers (PrusaSlicer "QUALITY" profile)
- 15% gyroid infill
- All 27 pieces in one print: load them together and use PrusaSlicer's **Arrange** (A) to fit them on the plate
- The tray as a separate print

**Notes:**
- Import at 100%. The units are mm.
- The pieces are oriented **roof-down**: the sloped top lies on the bed, so it comes out smooth. The walls overhang by at most 26.1°, so you don't need supports.
- PrusaSlicer may warn that the tall, narrow pieces could be unstable. On the MK3S+ it was safe to ignore, and none of the pieces came loose.
- Each piece edge is inset by 0.15 mm, which leaves about 0.3 mm between neighbours and 0.15 mm at the tray wall. Keep elephant's-foot compensation on.

**Tip:** an edge that matches at one end may not match at the other. Check both ends of every edge before you commit to a neighbour.

All our puzzles: [Tropical Geometry Puzzles by MaxPlusLab](https://www.printables.com/@Igor_2829688/collections/3919682) · More from [MaxPlusLab](https://github.com/maxpluslab) · Source and generator (MIT): https://github.com/maxpluslab/tropical-puzzle-lab
