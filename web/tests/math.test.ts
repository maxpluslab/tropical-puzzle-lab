import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { transform } from '../src/geometry/polygon';
import {
  formatCoefficient, intervals, parseCoefficient, parseTerms, polygonArea, polynomialCells,
  rationalCells, square, type Cell, type Convention,
} from '../src/math/tropical';
import type { Puzzle, Vec2 } from '../src/types';

interface Tropical {
  convention: Convention;
  domain: string;
  xyMmPerUnit: string;
  center?: [string, string];
  terms?: { id: string; a: number; b: number; c: string }[];
  numerator?: { id: string; a: number; b: number; c: string }[];
  denominator?: { id: string; a: number; b: number; c: string }[];
}

function load(id: string): Puzzle & { tropical: Tropical } {
  return JSON.parse(readFileSync(resolve(__dirname, '../../puzzles', id, 'puzzle.json'), 'utf8'));
}

function cellsOf(t: Tropical): Cell[] {
  const center = (t.center ?? ['0', '0']).map(parseCoefficient) as Vec2;
  const region = square(center, parseCoefficient(t.domain));
  return t.terms
    ? polynomialCells(parseTerms(t.terms), t.convention, region)
    : rationalCells(parseTerms(t.numerator!), parseTerms(t.denominator!), t.convention, region);
}

/** Each piece's reference footprint, back in domain coordinates. */
function referenceFootprints(puzzle: Puzzle & { tropical: Tropical }): Map<string, Vec2[]> {
  const t = puzzle.tropical;
  const s = parseCoefficient(t.xyMmPerUnit);
  const [cx, cy] = (t.center ?? ['0', '0']).map(parseCoefficient);
  return new Map(puzzle.pieces.map((piece, i) => [
    piece.id,
    transform(piece.polygon, puzzle.reference.poses[i]).map(([x, y]) => [x / s + cx, y / s + cy] as Vec2),
  ]));
}

describe('cells agree with the generator', () => {
  for (const id of ['new5', 'new1', 'rev2', 'rat1', 'rat2', 'cor1']) {
    it(id, () => {
      const puzzle = load(id);
      const cells = cellsOf(puzzle.tropical);
      const reference = referenceFootprints(puzzle);
      expect(cells.map((c) => c.id)).toEqual(puzzle.pieces.map((p) => p.id));
      for (const cell of cells) {
        const footprint = reference.get(cell.id)!;
        expect(polygonArea(cell.polygon)).toBeCloseTo(polygonArea(footprint), 6);
        // Every vertex of the generator's footprint is a vertex of ours.
        for (const [x, y] of footprint) {
          const nearest = Math.min(...cell.polygon.map(([u, v]) => Math.hypot(u - x, v - y)));
          expect(nearest).toBeLessThan(1e-6);
        }
      }
    });
  }
});

describe('one-variable example', () => {
  it('has its tropical roots at 1 and 3', () => {
    const terms = [{ id: 'A', a: 2, b: 0, c: 0 }, { id: 'B', a: 1, b: 0, c: 1 }, { id: 'C', a: 0, b: 0, c: 4 }];
    expect(intervals(terms, 'min', -1, 5)).toEqual([
      { id: 'A', from: -1, to: 1 }, { id: 'B', from: 1, to: 3 }, { id: 'C', from: 3, to: 5 },
    ]);
  });
});

describe('Hill 6a', () => {
  const t = load('new5').tropical;

  it('prints its coefficients as exact decimals', () => {
    expect(t.terms!.map((x) => formatCoefficient(x.c))).toEqual(['2.68', '5.91', '10.5', '8.49', '13.46', '18.66']);
    expect(formatCoefficient('-124/51')).toBe('-124/51');
  });
});

describe('Corrugated 27a', () => {
  const t = load('cor1').tropical;
  const numerator = parseTerms(t.numerator!);

  it('has a numerator that factors as a polynomial in x times a polynomial in y', () => {
    const coefficient = (a: number, b: number) => numerator.find((p) => p.a === a && p.b === b)!.c;
    for (const p of numerator) {
      expect(p.c).toBeCloseTo(coefficient(p.a, 0) + coefficient(3, p.b) - coefficient(3, 0), 9);
    }
  });
});
