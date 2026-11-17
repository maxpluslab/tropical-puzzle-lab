import { describe, expect, it } from 'vitest';
import { assemblies, solutionsHtml } from '../src/difficulty/rating';
import type { DifficultyRating } from '../src/types';

const rated = (solutions: number, exhaustive: boolean): DifficultyRating => ({ rating: 3, x: 3, nodes: 1000, exhaustive, solutions, diversity: 2 });

describe('the number of solutions', () => {
  it('is not mentioned for a puzzle with one solution', () => {
    expect(solutionsHtml(rated(1, true))).toBe('');
  });

  it('is exact for a finished search', () => {
    // rat2-flat: the search ran to its end and found two assemblies.
    expect(solutionsHtml(rated(2, true))).toContain('>2 solutions<');
    expect(assemblies(rated(101, true))).toBe('101');
  });

  it('is a lower bound for a search stopped at its limit', () => {
    // plt1-flat: stopped at 1.5 million nodes with 54 725 found; thousands set off by a thin space.
    expect(solutionsHtml(rated(54725, false))).toContain('>≥ 54 725 solutions<');
    expect(assemblies(rated(54725, false))).toBe('≥ 54 725');
  });

  it('is unknown when a stopped search found none', () => {
    // cor1-flat: no assembly within the limit; there is one, but the search did not reach it.
    expect(solutionsHtml(rated(0, false))).toBe('');
    expect(assemblies(rated(0, false))).toBe('?');
  });
});
