// Gallery: one card per construction, with its relief and flat modes. Thumbnails show the frame and a scrambled layout, never the reference assembly.
import { bounds, transform } from '../geometry/polygon';
import { scramble } from '../geometry/scramble';
import { escapeHtml } from '../player/player';
import { browserStore, loadSession } from '../sessions/session';
import { bindDifficulty, DIFFICULTY_PAGE, difficultyHtml, fetchIndex, solutionsHtml } from '../difficulty/rating';
import { constructions, MODES, puzzleHref } from './modes';
import { footerHtml } from '../footer';
import type { Puzzle, Variant, Vec2 } from '../types';

const base = import.meta.env.BASE_URL;

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${base}puzzles/${path}`);
  if (!response.ok) throw new Error(`${path}: ${response.status}`);
  return response.json();
}

function thumbnail(puzzle: Puzzle): string {
  const poses = scramble(puzzle, puzzle.scramble.defaultSeed);
  const pieces = puzzle.pieces.map((p, i) => transform(p.polygon, poses[i]));
  const target = puzzle.geometry.target.vertices;
  const box = bounds([...target, ...pieces.flat()]);
  const pad = 6;
  const points = (poly: Vec2[]) => poly.map(([x, y]) => `${x.toFixed(1)},${(-y).toFixed(1)}`).join(' ');
  return `<svg viewBox="${box.minX - pad} ${-box.maxY - pad} ${box.maxX - box.minX + 2 * pad} ${box.maxY - box.minY + 2 * pad}" role="img" aria-label="Scrambled pieces beside the empty tray">
    <polygon class="thumb-target" points="${points(target)}" />
    ${pieces.map((p) => `<polygon class="thumb-piece" points="${points(p)}" />`).join('')}
  </svg>`;
}

const MODE_KEY = 'tpl:gallery:mode';

/** Point each card at the preferred mode. The choice is a per-browser convenience; it never affects play. */
function applyMode(root: HTMLElement, mode: Variant): void {
  root.querySelectorAll<HTMLElement>('.card').forEach((card) => {
    const shown = card.querySelector<HTMLElement>(`[data-mode="${mode}"]`) ? mode : card.dataset.only!;
    card.querySelector<HTMLAnchorElement>('.card-link')!.href = card.querySelector<HTMLAnchorElement>(`[data-mode="${shown}"] .mode-link`)!.href;
    card.querySelectorAll<HTMLElement>('[data-mode]').forEach((row) => row.classList.toggle('preferred', row.dataset.mode === shown));
    card.querySelectorAll<HTMLElement>('[data-description]').forEach((p) => { p.hidden = p.dataset.description !== shown; });
  });
  root.querySelectorAll<HTMLButtonElement>('[data-open-in]').forEach((button) => {
    button.setAttribute('aria-pressed', String(button.dataset.openIn === mode));
  });
}

function savedMode(): Variant {
  try {
    const value = browserStore()?.getItem(MODE_KEY);
    return MODES.some(([m]) => m === value) ? (value as Variant) : 'relief';
  } catch {
    return 'relief';
  }
}

function progress(puzzle: Puzzle): string {
  const loaded = loadSession(puzzle, browserStore());
  if (loaded.status !== 'ok') return '';
  return loaded.session.solvedAt ? '<span class="progress solved">Solved</span>' : '<span class="progress">In progress</span>';
}

export async function renderGallery(root: HTMLElement): Promise<void> {
  root.innerHTML = `
    <div class="gallery">
      <header class="intro">
        <h1>Tropical Puzzle Lab</h1>
        <p class="challenge">Fill the square tray with every piece. In relief puzzles the sloped tops must also join into one continuous roof.</p>
        <p class="start-row" data-start hidden></p>
        <p class="intro-links"><a href="${base}?page=math">How the puzzles are made</a> · <a href="${base}?page=print">Make a physical puzzle</a></p>
      </header>
      <div class="filter" role="group" aria-label="Open puzzles in">
        <span class="filter-label">Open in</span>
        ${MODES.map(([m, label]) => `<button type="button" data-open-in="${m}">${label}</button>`).join('')}
      </div>
      <div class="cards" data-cards><p class="loading">Loading puzzles…</p></div>
      <section class="about" aria-labelledby="about-heading">
        <h2 id="about-heading">About the puzzles</h2>
        <p>Pieces can be moved and turned, but not flipped, and nothing snaps into place.
        Every puzzle can be played in <b>relief</b>, with sloped tops, or <b>flat</b>, with the heights removed. Choose a mode above or on a card, or switch inside the puzzle; each mode keeps its own progress.</p>
        <p>Most pieces are regions of a tropical polynomial: the maximum, or in some puzzles the minimum, of a few affine functions.
        In a rational puzzle they are the regions of a tropical quotient of two such polynomials, which is their ordinary difference.
        In relief, a piece's sloped top is its affine function, so a finished assembly forms one continuous roof: bowl-shaped for a maximum, rising to ridges for a minimum, with both valleys and ridges for a quotient.
        <a href="${base}?page=math">The mathematics behind the puzzles</a> explains this with interactive examples.</p>
        <p><b>Pleat puzzles are not tropical.</b> They are a related geometry and search experiment: a grid of triangles whose corners stand at just two heights,
        picked because a computer search finds them hard even with roofs. In relief, the search found just one assembly of each Pleat;
        flat, it found tens of thousands before it stopped, and any of them counts.</p>
        <p>The difficulty on each card, from 1 to 5, is an experimental rating of how much a computer search has to try before it has found every assembly among the placements it considers.
        Matching heights give most of the answer away, so most relief puzzles rate 1 while their flat versions rate much higher.
        A high rating can also mean many solutions, so a card shows how many the search found when there is more than one.
        It measures the search, not people: <a href="${DIFFICULTY_PAGE}">how difficulty is rated</a>.</p>
      </section>
      ${footerHtml()}
    </div>`;
  const cards = root.querySelector<HTMLElement>('[data-cards]')!;
  let mode = savedMode();
  applyMode(root, mode);
  root.querySelectorAll<HTMLButtonElement>('[data-open-in]').forEach((button) => {
    button.addEventListener('click', () => {
      mode = button.dataset.openIn as Variant;
      applyMode(root, mode);
      try {
        browserStore()?.setItem(MODE_KEY, mode);
      } catch {
        // Storage unavailable: the choice still works for this visit.
      }
    });
  });
  try {
    const index = await fetchIndex();
    const puzzles = new Map(
      await Promise.all(index.puzzles.map(async (e) => [e.id, await fetchJson<Puzzle>(e.path)] as const)),
    );
    // The title link stretches over the whole card, so the mode links and difficulty buttons sit on top of it.
    // The starter puzzle (index.json `starter`, set in its recipe) leads the intro and the cards.
    const starter = index.puzzles.find((e) => e.starter);
    if (starter) {
      const start = root.querySelector<HTMLElement>('[data-start]')!;
      start.innerHTML = `<a class="start" href="${puzzleHref(starter.id)}">Start here: ${escapeHtml(starter.name)}</a>
        <span class="start-note">${starter.pieceCount} pieces, a gentle first puzzle</span>`;
      start.hidden = false;
    }
    const groups = constructions(index);
    if (starter) groups.sort((a, b) => Number(Object.values(b).some((e) => e?.starter)) - Number(Object.values(a).some((e) => e?.starter)));
    cards.innerHTML = groups
      .map((modes) => {
        const present = MODES.filter(([m]) => modes[m]);
        const main = modes[present[0][0]]!;
        const first = puzzles.get(main.id)!;
        return `
        <article class="card" data-only="${present[0][0]}">
          ${thumbnail(first)}
          <div class="card-body">
            ${present.some(([m]) => modes[m]!.starter) ? '<p class="badge-start">Start here</p>' : ''}
            <h2><a class="card-link" href="${puzzleHref(main.id)}">${escapeHtml(main.name)}</a></h2>
            ${present.map(([m]) => `<p data-description="${m}">${escapeHtml(modes[m]!.description)}</p>`).join('')}
            <p class="meta">${first.pieces.length} pieces · ${escapeHtml(main.construction)} rev ${main.revision}</p>
            <ul class="card-modes">
              ${present.map(([m, label]) => `
                <li data-mode="${m}">
                  <a class="mode-link" href="${puzzleHref(modes[m]!.id)}">${label}</a>
                  ${difficultyHtml(modes[m]!.difficulty)}${solutionsHtml(modes[m]!.difficulty)}${progress(puzzles.get(modes[m]!.id)!)}
                </li>`).join('')}
            </ul>
          </div>
        </article>`;
      })
      .join('');
    bindDifficulty(root);
    applyMode(root, mode);
  } catch (error) {
    cards.innerHTML = `<p class="error">Could not load the puzzle list (${escapeHtml(String(error))}).</p>`;
  }
}
