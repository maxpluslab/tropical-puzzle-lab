// SVG figures for the mathematics page, as strings. Elements that take part in highlighting carry
// data-id (what they are) and data-rel (what they belong to); see linker.ts.
import type { Vec2 } from '../types';
import { centroid, formatNumber, type Cell, type Term } from './tropical';

const fmt = (v: number) => v.toFixed(2);
const attrs = (id: string, rel: string[] = []) => `data-id="${id}"${rel.length ? ` data-rel="${rel.join(' ')}"` : ''}`;

export interface RegionsOptions {
  /** Domain box [minX, minY, maxX, maxY]. */
  box: [number, number, number, number];
  ticks: number[];
  /** Label drawn in each cell; omitted when it returns ''. */
  label?: (cell: Cell) => string;
  /** Extra ids each cell belongs to (for example its terms). */
  rel?: (cell: Cell) => string[];
  /** Outlines drawn over the cells, such as the curves of P and Q. */
  overlays?: { polygons: Vec2[][]; className: string }[];
  labelSize?: number;
  title: string;
}

/** The cells in the plane, y up, with the domain's corners labelled. */
export function regionsSvg(cells: Cell[], o: RegionsOptions): string {
  const [minX, minY, maxX, maxY] = o.box;
  const size = 300, pad = 30;
  const sx = (x: number) => pad + ((x - minX) / (maxX - minX)) * size;
  const sy = (y: number) => pad + ((maxY - y) / (maxY - minY)) * size;
  const points = (poly: Vec2[]) => poly.map(([x, y]) => `${fmt(sx(x))},${fmt(sy(y))}`).join(' ');
  const labelSize = o.labelSize ?? 15;
  const polygons = cells.map((c) => `<polygon class="cell" ${attrs(c.id, o.rel?.(c))} points="${points(c.polygon)}"><title>${c.id}</title></polygon>`).join('');
  const labels = cells.map((c) => {
    const text = o.label ? o.label(c) : c.id;
    if (!text) return '';
    const [x, y] = centroid(c.polygon);
    return `<text class="cell-label" x="${fmt(sx(x))}" y="${fmt(sy(y))}" font-size="${labelSize}">${text}</text>`;
  }).join('');
  const overlays = (o.overlays ?? []).map((layer) => layer.polygons.map((p) => `<polygon class="${layer.className}" points="${points(p)}" />`).join('')).join('');
  const ticks = o.ticks.map((t) => `
    <text class="tick" x="${fmt(sx(t))}" y="${pad + size + 18}" text-anchor="middle">${formatNumber(t)}</text>
    <text class="tick" x="${pad - 6}" y="${fmt(sy(t) + 4)}" text-anchor="end">${formatNumber(t)}</text>`).join('');
  return `<svg class="regions" viewBox="0 0 ${size + 2 * pad} ${size + 2 * pad}" role="img" aria-label="${o.title}">
    ${polygons}${overlays}
    <rect class="frame" x="${pad}" y="${pad}" width="${size}" height="${size}" />
    ${labels}${ticks}
    <text class="axis-name" x="${pad + size + 8}" y="${pad + size + 4}">x</text>
    <text class="axis-name" x="${pad}" y="${pad - 8}" text-anchor="middle">y</text>
  </svg>`;
}

export interface GraphOptions {
  lo: number;
  hi: number;
  /** The bold graph, affine between consecutive breakpoints. */
  fn: (x: number) => number;
  breaks: number[];
  /** Which piece of the band a segment belongs to, by its midpoint. */
  band?: { id: string; from: number; to: number; rel?: string[] }[];
  /** Faint full lines for the individual terms. */
  lines?: Term[];
  /** Marked points on the x-axis. */
  marks?: { x: number; label: string; className?: string }[];
  ticks: number[];
  variable?: string;
  /** Range of the vertical axis; by default the graph's range with some room. */
  yRange?: [number, number];
  title: string;
}

/** The graph of a piecewise-affine function of one variable, with the intervals beneath it. */
export function graphSvg(o: GraphOptions): string {
  const width = 360, height = 220, left = 16, right = 26, top = 12, plotH = 150, bandH = 22;
  const plotW = width - left - right;
  const xs = [o.lo, ...o.breaks.filter((b) => b > o.lo && b < o.hi), o.hi];
  const values = xs.map(o.fn);
  const [yLo, yHi] = o.yRange ?? (() => {
    const lo = Math.min(...values), hi = Math.max(...values), room = (hi - lo) * 0.18 || 1;
    return [lo - room, hi + room];
  })();
  const sx = (x: number) => left + ((x - o.lo) / (o.hi - o.lo)) * plotW;
  const sy = (y: number) => top + ((yHi - y) / (yHi - yLo)) * plotH;
  const clipId = `clip-${Math.random().toString(36).slice(2, 8)}`;
  const bandAt = (x: number) => o.band?.find((b) => x >= b.from - 1e-9 && x <= b.to + 1e-9);

  const lines = (o.lines ?? []).map((t) => {
    const coords = `x1="${fmt(sx(o.lo))}" y1="${fmt(sy(t.c + t.a * o.lo))}" x2="${fmt(sx(o.hi))}" y2="${fmt(sy(t.c + t.a * o.hi))}"`;
    return `<line class="term-line" ${attrs(t.id)} ${coords} /><line class="hit" ${attrs(t.id)} ${coords}><title>${t.id}</title></line>`;
  }).join('');
  const segments = xs.slice(0, -1).map((x0, i) => {
    const x1 = xs[i + 1];
    const piece = bandAt((x0 + x1) / 2);
    return `<line class="graph-seg" ${piece ? attrs(piece.id, piece.rel) : ''} x1="${fmt(sx(x0))}" y1="${fmt(sy(values[i]))}" x2="${fmt(sx(x1))}" y2="${fmt(sy(values[i + 1]))}" />`;
  }).join('');
  const bandY = top + plotH + 6;
  const band = (o.band ?? []).map((b) => {
    const x0 = sx(Math.max(b.from, o.lo)), x1 = sx(Math.min(b.to, o.hi));
    return `<rect class="band" ${attrs(b.id, b.rel)} x="${fmt(x0)}" y="${bandY}" width="${fmt(x1 - x0)}" height="${bandH}"><title>${b.id}</title></rect>
      ${x1 - x0 > 14 ? `<text class="band-label" x="${fmt((x0 + x1) / 2)}" y="${bandY + bandH / 2 + 4}">${b.id}</text>` : ''}`;
  }).join('');
  const marks = (o.marks ?? []).map((m) => `
    <line class="mark ${m.className ?? ''}" x1="${fmt(sx(m.x))}" x2="${fmt(sx(m.x))}" y1="${top}" y2="${top + plotH}" />
    <text class="mark-label ${m.className ?? ''}" x="${fmt(sx(m.x))}" y="${top + plotH - 5}" dx="3">${m.label}</text>`).join('');
  const axisY = bandY + bandH + 14;
  const ticks = o.ticks.map((t) => `<text class="tick" x="${fmt(sx(t))}" y="${axisY}" text-anchor="middle">${formatNumber(t)}</text>`).join('');
  return `<svg class="graph" viewBox="0 0 ${width} ${height}" role="img" aria-label="${o.title}">
    <defs><clipPath id="${clipId}"><rect x="${left}" y="${top}" width="${plotW}" height="${plotH}" /></clipPath></defs>
    <rect class="plot" x="${left}" y="${top}" width="${plotW}" height="${plotH}" />
    ${marks}
    <g clip-path="url(#${clipId})">${lines}${segments}</g>
    ${band}${ticks}
    <text class="axis-name" x="${left + plotW + 8}" y="${axisY}">${o.variable ?? 'x'}</text>
  </svg>`;
}
