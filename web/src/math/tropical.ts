// Tropical polynomials and rational functions in two variables, in floating point, for the
// mathematics page. The generator computes the puzzles exactly; tests/math.test.ts checks that
// these cells agree with the committed puzzle.json files.
import type { Vec2 } from '../types';

export type Convention = 'max' | 'min';

/** The term c + a·x + b·y, written c ⊙ x^a ⊙ y^b tropically. */
export interface Term {
  id: string;
  a: number;
  b: number;
  c: number;
}

/** A two-dimensional cell and the affine function F equals on it. */
export interface Cell {
  id: string;
  polygon: Vec2[];
  /** F = c + a·x + b·y on this cell. */
  f: { a: number; b: number; c: number };
  /** The terms that win on this cell: one for a polynomial, the numerator and denominator term for a rational function. */
  terms: string[];
}

/** "67/25", "-10.353781" or "12" as a number. */
export function parseCoefficient(text: string): number {
  const [num, den] = text.split('/');
  return den === undefined ? Number(num) : Number(num) / Number(den);
}

export function parseTerms(raw: { id: string; a: number; b: number; c: string }[]): Term[] {
  return raw.map((t) => ({ id: t.id, a: t.a, b: t.b, c: parseCoefficient(t.c) }));
}

export function termValue(t: Term, x: number, y: number): number {
  return t.c + t.a * x + t.b * y;
}

export function evaluate(terms: Term[], convention: Convention, x: number, y: number): number {
  const values = terms.map((t) => termValue(t, x, y));
  return convention === 'max' ? Math.max(...values) : Math.min(...values);
}

export function square(center: Vec2, halfWidth: number): Vec2[] {
  const [cx, cy] = center;
  return [[cx - halfWidth, cy - halfWidth], [cx + halfWidth, cy - halfWidth], [cx + halfWidth, cy + halfWidth], [cx - halfWidth, cy + halfWidth]];
}

/** Keep the part of a convex polygon where p·x + q·y + r ≥ 0. */
function clipHalfPlane(poly: Vec2[], p: number, q: number, r: number): Vec2[] {
  const out: Vec2[] = [];
  const side = ([x, y]: Vec2) => p * x + q * y + r;
  for (let i = 0; i < poly.length; i++) {
    const a = poly[i];
    const b = poly[(i + 1) % poly.length];
    const fa = side(a);
    const fb = side(b);
    if (fa >= 0) out.push(a);
    if ((fa > 0 && fb < 0) || (fa < 0 && fb > 0)) {
      const t = fa / (fa - fb);
      out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]);
    }
  }
  return out;
}

export function polygonArea(poly: Vec2[]): number {
  let sum = 0;
  for (let i = 0; i < poly.length; i++) {
    const [x0, y0] = poly[i];
    const [x1, y1] = poly[(i + 1) % poly.length];
    sum += x0 * y1 - x1 * y0;
  }
  return sum / 2;
}

export function centroid(poly: Vec2[]): Vec2 {
  let a = 0, cx = 0, cy = 0;
  for (let i = 0; i < poly.length; i++) {
    const [x0, y0] = poly[i];
    const [x1, y1] = poly[(i + 1) % poly.length];
    const w = x0 * y1 - x1 * y0;
    a += w;
    cx += (x0 + x1) * w;
    cy += (y0 + y1) * w;
  }
  return [cx / (3 * a), cy / (3 * a)];
}

const MIN_AREA = 1e-9;

/** Drop repeated vertices left by clipping through a corner. */
function tidy(poly: Vec2[]): Vec2[] {
  return poly.filter((p, i) => {
    const q = poly[(i + 1) % poly.length];
    return Math.hypot(p[0] - q[0], p[1] - q[1]) > 1e-9;
  });
}

/** The part of `region` where `term` attains the max (or min) of `terms`, or null if it has no area there. */
function winningRegion(term: Term, terms: Term[], convention: Convention, region: Vec2[]): Vec2[] | null {
  const sign = convention === 'max' ? 1 : -1;
  let poly = region;
  for (const other of terms) {
    if (other === term) continue;
    poly = clipHalfPlane(poly, sign * (term.a - other.a), sign * (term.b - other.b), sign * (term.c - other.c));
    if (poly.length < 3) return null;
  }
  poly = tidy(poly);
  return poly.length >= 3 && polygonArea(poly) > MIN_AREA ? poly : null;
}

/** The cells of a tropical polynomial inside `region`, in term order: each is where one term wins. */
export function polynomialCells(terms: Term[], convention: Convention, region: Vec2[]): Cell[] {
  return terms.flatMap((t) => {
    const polygon = winningRegion(t, terms, convention, region);
    return polygon ? [{ id: t.id, polygon, f: { a: t.a, b: t.b, c: t.c }, terms: [t.id] }] : [];
  });
}

/**
 * The cells of P ⊘ Q = P − Q: the common refinement of P's and Q's cells, numerator-major, with ids
 * p.id + q.id as in the generator. On the cell of p and q, F is the affine function p − q.
 */
export function rationalCells(numerator: Term[], denominator: Term[], convention: Convention, region: Vec2[]): Cell[] {
  return polynomialCells(numerator, convention, region).flatMap((pCell) => {
    const p = numerator.find((t) => t.id === pCell.id)!;
    return polynomialCells(denominator, convention, pCell.polygon).map((qCell) => {
      const q = denominator.find((t) => t.id === qCell.id)!;
      return { id: p.id + q.id, polygon: qCell.polygon, f: { a: p.a - q.a, b: p.b - q.b, c: p.c - q.c }, terms: [p.id, q.id] };
    });
  });
}

/** Smallest and largest value of F on the cells (attained at their vertices, since F is affine on each). */
export function range(cells: Cell[]): [number, number] {
  let lo = Infinity, hi = -Infinity;
  for (const cell of cells) {
    for (const [x, y] of cell.polygon) {
      const v = cell.f.c + cell.f.a * x + cell.f.b * y;
      lo = Math.min(lo, v);
      hi = Math.max(hi, v);
    }
  }
  return [lo, hi];
}

/** One-variable pieces of a tropical polynomial on [lo, hi]: the intervals where each term wins, left to right. */
export function intervals(terms: Term[], convention: Convention, lo: number, hi: number): { id: string; from: number; to: number }[] {
  const out: { id: string; from: number; to: number }[] = [];
  for (const t of terms) {
    let from = lo, to = hi;
    for (const o of terms) {
      if (o === t) continue;
      // t wins over o where s·((t.c − o.c) + (t.a − o.a)·x) ≥ 0.
      const s = convention === 'max' ? 1 : -1;
      const k = s * (t.a - o.a);
      const m = s * (t.c - o.c);
      if (k === 0) {
        if (m < 0) { from = Infinity; break; }
        continue;
      }
      const root = -m / k;
      if (k > 0) from = Math.max(from, root);
      else to = Math.min(to, root);
    }
    if (to - from > 1e-9) out.push({ id: t.id, from, to });
  }
  return out.sort((p, q) => p.from - q.from);
}

/** Exact decimal for a coefficient string when it terminates within six places, otherwise the fraction. */
export function formatCoefficient(text: string): string {
  const value = parseCoefficient(text);
  for (let places = 0; places <= 6; places++) {
    const scaled = value * 10 ** places;
    if (Math.abs(scaled - Math.round(scaled)) < 1e-9) return value.toFixed(places);
  }
  return text;
}

/** A number for display, with a true minus sign. */
export function formatNumber(value: number, places = 2): string {
  const text = Number(value.toFixed(places)).toString();
  return text.replace('-', '−');
}
