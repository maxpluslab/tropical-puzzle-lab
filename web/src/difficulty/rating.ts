// Difficulty pips with a link to how it is calculated. The link appears on hover, while the
// widget has keyboard focus, or after a tap/click on the pips (hover does not exist on touch screens).
import type { DifficultyRating, PuzzleIndex } from '../types';

const base = import.meta.env.BASE_URL;
export const DIFFICULTY_PAGE = `${base}?page=difficulty`;

export function pips(rating: number): string {
  return `<span class="pips" aria-hidden="true">${[1, 2, 3, 4, 5].map((i) => `<i${i <= rating ? ' class="on"' : ''}></i>`).join('')}</span>`;
}

/** A count as a reader reads it, thousands set off by thin spaces: 54 725. */
export function formatCount(n: number): string {
  return n.toLocaleString('en-GB').replace(/,/g, ' ');
}

/** Assemblies found: exact for a finished search, a lower bound (≥) for one that stopped after finding some, otherwise unknown. */
export function assemblies(d: DifficultyRating): string {
  if (d.exhaustive) return formatCount(d.solutions);
  return d.solutions > 0 ? `≥ ${formatCount(d.solutions)}` : '?';
}

/**
 * A note for puzzles with more than one assembly: any of them completes the puzzle. Empty for one.
 * A search stopped at its node limit has found at least that many, so the count gets "≥".
 */
export function solutionsHtml(d: DifficultyRating): string {
  if (d.solutions <= 1) return '';
  const count = `${d.exhaustive ? '' : '≥ '}${formatCount(d.solutions)}`;
  const title = d.exhaustive
    ? `The search found ${count} different assemblies; any of them completes the puzzle.`
    : `The search found ${count} different assemblies before it stopped, and there may be more; any of them completes the puzzle.`;
  return `<span class="solutions" title="${title}">${count} solutions</span>`;
}

/** `placement` is where the link pops up relative to the pips. */
export function difficultyHtml(d: DifficultyRating, placement: 'above' | 'below' = 'above'): string {
  return `<span class="difficulty difficulty-${placement}" data-difficulty>
    <button type="button" class="difficulty-pill" aria-expanded="false">
      <span class="difficulty-label">Difficulty</span>${pips(d.rating)}<span class="visually-hidden">${d.rating} of 5</span>
    </button>
    <span class="difficulty-pop"><a href="${DIFFICULTY_PAGE}">Rated by computer search effort: how?</a></span>
  </span>`;
}

function setOpen(widget: Element, open: boolean): void {
  widget.classList.toggle('open', open);
  widget.querySelector('.difficulty-pill')?.setAttribute('aria-expanded', String(open));
}

/** Tap or click on the pips toggles the link; a click anywhere else closes it. Call once per page. */
export function bindDifficulty(root: HTMLElement): void {
  document.addEventListener('click', (event) => {
    const pill = (event.target as Element).closest?.('.difficulty-pill');
    const current = pill?.closest('[data-difficulty]');
    root.querySelectorAll('[data-difficulty].open').forEach((w) => w !== current && setOpen(w, false));
    if (pill && current && root.contains(current)) {
      event.preventDefault();
      setOpen(current, !current.classList.contains('open'));
    }
  });
}

export async function fetchIndex(): Promise<PuzzleIndex> {
  const response = await fetch(`${base}puzzles/index.json`);
  if (!response.ok) throw new Error(`index.json: ${response.status}`);
  return response.json();
}

/** Fill a placeholder with a rating whose link pops up below it. */
export function showDifficulty(root: HTMLElement, slot: HTMLElement, d: DifficultyRating): void {
  slot.innerHTML = difficultyHtml(d, 'below') + solutionsHtml(d);
  bindDifficulty(root);
}
