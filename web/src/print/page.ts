// How to make a physical puzzle. The published listings and the puzzle list are read from
// index.json (a variant's `printables` URL comes from its recipe), so the page cannot drift
// from the puzzles. Print figures here are the defaults of `tpl-stl` (generator/stl.py).
import { pips, fetchIndex } from '../difficulty/rating';
import { escapeHtml } from '../player/player';
import type { PuzzleIndex, PuzzleIndexEntry } from '../types';

const base = import.meta.env.BASE_URL;
const REPO = 'https://github.com/maxpluslab/tropical-puzzle-lab';

const playHref = (e: PuzzleIndexEntry): string => `${base}?puzzle=${encodeURIComponent(e.id)}`;
const external = (href: string, text: string): string =>
  `<a href="${escapeHtml(href)}" target="_blank" rel="noopener">${escapeHtml(text)}</a>`;

/** Variants with a published print listing, in index order. */
export function published(index: PuzzleIndex): PuzzleIndexEntry[] {
  return index.puzzles.filter((e) => e.printables);
}

function publishedRows(entries: PuzzleIndexEntry[]): string {
  return entries
    .map((e) => `<tr>
      <td><a href="${playHref(e)}">${escapeHtml(e.code)}</a></td>
      <td class="num">${e.pieceCount}</td>
      <td>${pips(e.difficulty.rating)} ${e.difficulty.rating}</td>
      <td>${external(e.printables!, 'Printables')}</td>
    </tr>`)
    .join('');
}

function allRows(index: PuzzleIndex): string {
  return index.puzzles
    .map((e) => `<tr>
      <td><a href="${playHref(e)}">${escapeHtml(e.code)}</a></td>
      <td>${e.variant === 'relief' ? 'relief' : 'flat'}</td>
      <td class="num">${e.pieceCount}</td>
      <td><code>tpl-stl ${escapeHtml(e.id)}</code></td>
    </tr>`)
    .join('');
}

export function printPageHtml(index: PuzzleIndex): string {
  const listed = published(index);
  return `
    <p>Every puzzle in the gallery can be 3D-printed: a square tray and one solid per piece, with the same shapes and,
    for relief puzzles, the same sloped tops as on screen. A few have been printed and published with ready-made files;
    any other can be generated from the source.</p>

    <h2>Ready to print</h2>
    ${listed.length
      ? `<p>These have been printed and are published on Printables, with STL files and print notes:</p>
        <div class="table-wrap"><table class="data">
          <thead><tr><th>Puzzle</th><th class="num">Pieces</th><th>Difficulty</th><th>Files</th></tr></thead>
          <tbody>${publishedRows(listed)}</tbody>
        </table></div>`
      : '<p>None published yet.</p>'}

    <h2>Our print settings</h2>
    <p>The published puzzles were printed on a Prusa MK3S+:</p>
    <ul>
      <li>PLA, 0.4 mm nozzle</li>
      <li>0.20 mm layers (PrusaSlicer “QUALITY” profile)</li>
      <li>15% gyroid infill</li>
      <li>All pieces in one print, laid out with PrusaSlicer's <b>Arrange</b> (A); the tray as a separate print</li>
    </ul>
    <p>PrusaSlicer may warn that tall, narrow pieces could be unstable. It was safe to ignore: no piece came loose.</p>

    <h2>Make your own</h2>
    <p>The STL files are generated from the same data as the website, by the generator in the
    ${external(REPO, 'source repository')}. You need Git and Python 3.10 or later; the generator has no other dependencies.</p>
    <pre><code>git clone ${REPO}.git
cd tropical-puzzle-lab
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\\Scripts\\activate
pip install -e generator
tpl-stl new2                  # relief pieces of Hill 16b
tpl-stl new2-flat             # the same footprints, all 12 mm thick</code></pre>
    <p><code>tpl-stl &lt;id&gt;</code> writes <code>print/&lt;id&gt;/</code>: one <code>piece-&lt;name&gt;.stl</code> per piece,
    <code>tray.stl</code>, and <code>SETTINGS.txt</code>, which records the puzzle, its exact geometry and the largest overhang.
    The ids are listed at the bottom of this page.</p>
    <ul>
      <li><b>Orientation.</b> Pieces are turned roof-down, so the sloped top is printed against the bed and comes out smooth.
      The side walls then lean by the roof's tilt, at most 28° in the current puzzles (<code>SETTINGS.txt</code> gives each puzzle's figure), so no supports are needed.
      <code>--orientation underside-down</code> keeps them the way they sit in the tray.</li>
      <li><b>Clearance.</b> Each piece edge is moved inward by 0.15 mm (<code>--xy-inset</code>), leaving about 0.3 mm between
      neighbours and 0.15 mm at the tray wall. Heights are not changed. Keep your slicer's elephant's-foot compensation on.</li>
      <li><b>Tray.</b> A 144 mm square cavity, 7 mm deep, with 4 mm walls and a 3 mm floor (<code>--wall</code>, <code>--floor</code>):
      152 × 152 × 10 mm overall. Relief and flat versions use the same tray.</li>
      <li><b>Units.</b> Millimetres; import at 100%.</li>
    </ul>
    <p>In a flat version every piece is 12 mm thick, so it uses less filament than the relief version, whose pieces are 8 to 43 mm thick.</p>

    <h2>All puzzles</h2>
    <div class="table-wrap"><table class="data">
      <thead><tr><th>Puzzle</th><th>Mode</th><th class="num">Pieces</th><th>Command</th></tr></thead>
      <tbody>${allRows(index)}</tbody>
    </table></div>`;
}

export async function renderPrintPage(root: HTMLElement): Promise<void> {
  document.title = 'Make a physical puzzle · Tropical Puzzle Lab';
  root.innerHTML = `
    <div class="gallery doc">
      <a class="back" href="${base}">← Gallery</a>
      <header class="intro"><h1>Make a physical puzzle</h1></header>
      <div data-doc><p class="loading">Loading…</p></div>
    </div>`;
  const doc = root.querySelector<HTMLElement>('[data-doc]')!;
  try {
    doc.innerHTML = printPageHtml(await fetchIndex());
  } catch (error) {
    doc.innerHTML = `<p class="error">Could not load the puzzle list (${escapeHtml(String(error))}).</p>`;
  }
}
