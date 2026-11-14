# Printables listings

Each puzzle variant published on [Printables](https://www.printables.com/) has its own listing; relief and flat are never combined, because the two piece sets are easy to mix up. The text of each listing is kept in `puzzles/<id>/printables.md` (for example [`puzzles/new2/printables.md`](../puzzles/new2/printables.md)), so listings stay consistent and can be updated in one place. Write new listings from the template below.

## Conventions

- **Name:** `Tropical Puzzle <code>: <n>-piece relief tiling puzzle` (or `flat tiling puzzle`), where `<code>` is the variant code from [puzzle-format.md](puzzle-format.md#names), e.g. `Hill 16b-r`.
- **Summary:** at most 120 characters, including the gallery link `https://maxpluslab.github.io/tropical-puzzle-lab/` (49 characters). Count it before publishing.
- **Description:** the sections below, in this order. Link the gallery, the puzzle's direct link (`?puzzle=<id>`), the mathematics page and the organization [MaxPlusLab](https://github.com/maxpluslab).
- **Tags:** the core set on every listing, in this order: `puzzle`, `tiling puzzle`, `jigsaw`, `brain teaser`, `tray puzzle`, `mathematical puzzle`, `math`, `tropical geometry`. Don't tag difficulty (`easy`, `hard`, ratings): it would contradict the online rating if that changes.
- **Organization name:** write **MaxPlusLab**, capitalized like that, in all text. Only URLs (`github.com/maxpluslab`, `maxpluslab.github.io`) are lower case.
- **Printing:** quote only settings that were actually printed, and say which printer. The figures (piece sizes, overhang, inset, tray size) come from `tpl-stl`'s `SETTINGS.txt` and the STL files; don't estimate them. Piece thickness comes from the roofs in `puzzle.json`, not from the STLs: those are roof-down, so their bounding boxes are not heights in the tray. Don't claim a fit test that wasn't done.
- **No spoilers:** never use a photo or render of the solved puzzle as the cover, in keeping with the rule that the reference assembly is never shown.
- **Credits:** no personal attribution until the collaborators have agreed the text (see the README).
- **After publishing:** add the listing's URL to the variant in `recipe.json` as `"printables"` and rerun `tpl-export`. It then appears on the website's [Make a physical puzzle](https://maxpluslab.github.io/tropical-puzzle-lab/?page=print) page (`?page=print`), and the player lists it under *Print*. Print settings on that page (`web/src/print/page.ts`) should match the listings. Record the URL at the top of `puzzles/<id>/printables.md` too.
- **Collection:** add every listing to the collection [Tropical Geometry Puzzles by MaxPlusLab](https://www.printables.com/@Igor_2829688/collections/3919682) (below).
- **Files:** upload the contents of `print/<id>/` except `SETTINGS.txt`, which is a generator report rather than instructions.

## Collection

Published: https://www.printables.com/@Igor_2829688/collections/3919682

**Name** (at most 40 characters): Tropical Geometry Puzzles by MaxPlusLab

**Description:**

3D-printable tiling puzzles built from tropical geometry, by [MaxPlusLab](https://github.com/maxpluslab).

Each piece is a region where one plane is the largest (or smallest) of a set of planes, so the pieces are convex and the cuts between them form a tropical curve. In the relief puzzles, each piece's sloped top is its own plane. The puzzle is solved when the pieces fill the square tray and every pair of neighbours meets at the same height, so the tops join into one continuous roof: a hill, a landscape of peaks and pits, or a corrugated sheet.

All puzzles share the same 144 mm tray design, print without supports, and can be played free in your browser first, with a flat mode where the heights are removed: https://maxpluslab.github.io/tropical-puzzle-lab/

Puzzle names give the roof shape, the number of pieces and a letter, plus -r for relief or -f for flat: Hill 16b-r is a 16-piece hill in relief.

Every puzzle on the website can be printed, not just the ones in this collection. The generator and instructions are open source (MIT): https://github.com/maxpluslab/tropical-puzzle-lab

## Template

```markdown
**Name:** Tropical Puzzle <code>: <n>-piece <relief|flat> tiling puzzle

**Summary:** <≤120 characters, ending with the gallery link>

**Tags:** <the core set>

**Description:**

<code> is a 3D-printable puzzle from [Tropical Puzzle Lab](https://maxpluslab.github.io/tropical-puzzle-lab/),
a project of [MaxPlusLab](https://github.com/maxpluslab) that builds puzzles from tropical geometry. <pieces, sizes, tray>

<When the puzzle is solved.>

<What makes it hard; the online difficulty rating.>

**The mathematics.** <The function, what a piece is, what the roof or seams look like.>

**Play online:** <gallery link> (this puzzle: <direct link>; <note on the other mode>) · How it works: <math page link>

**Files:** <tray and pieces, with sizes>

**Printing.** Tested on <printer> with these settings:
- <material, nozzle>
- <layer height, profile>
- <infill>
- <plate layout>

**Notes:**
- Import at 100%. The units are mm.
- <orientation and supports>
- <slicer warnings seen and whether they mattered>
- <inset and clearance>

**Tip:** <one hint that doesn't give the solution away>

All our puzzles: [Tropical Geometry Puzzles by MaxPlusLab](https://www.printables.com/@Igor_2829688/collections/3919682) · More from [MaxPlusLab](https://github.com/maxpluslab) · Source and generator (MIT): https://github.com/maxpluslab/tropical-puzzle-lab
```
