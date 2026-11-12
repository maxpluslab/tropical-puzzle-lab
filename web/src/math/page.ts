// The mathematics behind the puzzles. The 6 intro and 27 corrugated examples are read from their
// generated puzzle.json, so the page cannot drift from the puzzles. Only 6 intro is drawn openly:
// drawing a puzzle's cells shows its solution, so the 27 corrugated figures stay covered until the
// reader asks for them, and the rational example is a small function that is not in the gallery.
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { escapeHtml } from '../player/player';
import type { Puzzle, Vec2 } from '../types';
import { graphSvg, regionsSvg } from './figures';
import { Linker } from './linker';
import { createRelief, type ReliefScale } from './relief';
import {
  evaluate, formatNumber, intervals, parseCoefficient, parseTerms, polynomialCells,
  rationalCells, square, type Cell, type Convention, type Term,
} from './tropical';

const base = import.meta.env.BASE_URL;

interface RawTerm { id: string; a: number; b: number; c: string }
interface TropicalPuzzle extends Puzzle {
  tropical: { convention: Convention; domain: string; xyMmPerUnit: string; center?: [string, string]; terms?: RawTerm[]; numerator?: RawTerm[]; denominator?: RawTerm[] };
}

// ---------------------------------------------------------------- formulas

const tex = (source: string, displayMode = false): string => katex.renderToString(source, {
  displayMode, throwOnError: false, strict: 'ignore', trust: (context) => context.command === '\\htmlData',
});
const math = (source: string): string => tex(source, true);

/** A number in TeX, rounded to `places` decimals. */
const num = (v: number, places = 2): string => formatNumber(v, places).replace('−', '-');

/** c + a·x + b·y in TeX, without zero terms or unit coefficients. */
function affine(c: number, a: number, b: number, vars: [string, string] = ['x', 'y'], places = 2): string {
  const parts: string[] = [];
  const push = (k: number, v: string) => {
    if (k === 0) return;
    const mag = Math.abs(k) === 1 && v ? '' : num(Math.abs(k), places);
    parts.push(`${k < 0 ? '-' : parts.length ? '+' : ''}${mag}${v}`);
  };
  push(c, '');
  push(a, vars[0]);
  push(b, vars[1]);
  return parts.length ? parts.join(' ') : '0';
}

/** c ⊙ x^a ⊙ y^b in TeX. */
function monomial(c: number, a: number, b: number, places = 2): string {
  const power = (v: string, k: number) => (k === 0 ? [] : [k === 1 ? v : `${v}^{${k}}`]);
  const factors = [...power('x', a), ...power('y', b)];
  const coefficient = c === 0 && factors.length ? [] : [c < 0 ? `(${num(c, places)})` : num(c, places)];
  return [...coefficient, ...factors].join(' \\odot ');
}

const link = (id: string, body: string) => `\\htmlData{id=${id}}{${body}}`;
const named = (id: string, body: string) => link(id, `\\underset{\\scriptscriptstyle ${id}}{${body}}`);

function classical(terms: Term[], convention: Convention, places = 2, label = true): string {
  return `\\${convention}\\bigl(${terms.map((t) => (label ? named : link)(t.id, affine(t.c, t.a, t.b, ['x', 'y'], places))).join(',\\ ')}\\bigr)`;
}

function tropical(terms: Term[], places = 2): string {
  return terms.map((t) => link(t.id, monomial(t.c, t.a, t.b, places))).join(' \\oplus ');
}

/** Items in groups of `size`, one group per line, so long formulas fit a phone. */
function groups(items: string[], separator: string, size = 2): string[] {
  const lines: string[] = [];
  for (let i = 0; i < items.length; i += size) lines.push(items.slice(i, i + size).join(separator));
  return lines;
}

/** lhs = t1 ⊕ t2 / ⊕ t3 ⊕ … over aligned lines. */
function tropicalLines(lhs: string, terms: Term[]): string {
  const lines = groups(terms.map((t) => link(t.id, monomial(t.c, t.a, t.b))), ' \\oplus ');
  return `\\begin{aligned} ${lhs} = {}& ${lines.join(' \\\\ & \\oplus ')} \\end{aligned}`;
}

/** lhs = max(item, item, / item, …) over aligned lines, with the items already in TeX. */
function extremumLines(lhs: string, items: string[], convention: Convention, end = '', size = 2): string {
  // Braces keep a leading minus unary when an item starts a line.
  const lines = groups(items.map((item) => `{${item}}`), ',\\ ', size);
  return `\\begin{aligned} ${lhs} = \\${convention}\\bigl(& ${lines.join(', \\\\ & ')} \\bigr)${end} \\end{aligned}`;
}

function classicalLines(lhs: string, terms: Term[], convention: Convention): string {
  return extremumLines(lhs, terms.map((t) => named(t.id, affine(t.c, t.a, t.b))), convention);
}

// ---------------------------------------------------------------- page pieces

function figure(content: string, caption: string, className = ''): string {
  return `<figure class="fig ${className}">${content}<figcaption>${caption}</figcaption></figure>`;
}

function relief(id: string): string {
  return `<div class="relief" data-relief="${id}"></div>`;
}

async function fetchPuzzle(id: string): Promise<TropicalPuzzle> {
  const response = await fetch(`${base}puzzles/${id}/puzzle.json`);
  if (!response.ok) throw new Error(`${id}: ${response.status}`);
  return response.json();
}

/** Small counts in words, as in running text. */
const words = (n: number): string =>
  ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen'][n] ?? String(n);

const href = (id: string) => `${base}?puzzle=${encodeURIComponent(id)}`;

/** Everything the 6 intro sections need. */
function intro(puzzle: TropicalPuzzle) {
  const t = puzzle.tropical;
  const terms = parseTerms(t.terms!);
  const convention = t.convention;
  const center = (t.center ?? ['0', '0']).map(parseCoefficient) as Vec2;
  const half = parseCoefficient(t.domain);
  const cells = polynomialCells(terms, convention, square(center, half));
  const box: [number, number, number, number] = [center[0] - half, center[1] - half, center[0] + half, center[1] + half];
  const ticks = [box[0], center[0], box[2]];
  const scale: ReliefScale = {
    mmPerUnit: parseCoefficient(t.xyMmPerUnit), center,
    minThicknessMm: puzzle.geometry.minThicknessMm ?? 8, reliefMm: puzzle.geometry.reliefMm ?? 35,
  };
  return { t, terms, convention, center, half, cells, box, ticks, scale };
}

function arithmeticSection(): string {
  return `
    <h2 id="arithmetic">1. Tropical arithmetic</h2>
    <p>Tropical arithmetic replaces the usual operation of addition with minimum, and the usual operation of multiplication with addition:</p>
    ${math('a \\oplus b = \\min(a, b), \\qquad a \\odot b = a + b.')}
    <p>So ${tex('3 \\oplus 5 = 3')} and ${tex('3 \\odot 5 = 8')}. Both operations are commutative and associative, and ${tex('\\odot')} distributes over ${tex('\\oplus')}:
    for example, ${tex('1 \\odot (3 \\oplus 5) = 1 \\odot 3 \\oplus 1 \\odot 5 = 4')}.
    The tropical zero is ${tex('\\infty')}, since ${tex('a \\oplus \\infty = a')}, and the tropical one is ${tex('0')}, since ${tex('a \\odot 0 = a')}.
    Tropical division ${tex('a \\oslash b = a - b')} always works, but there is no tropical subtraction: no ${tex('b')} gives ${tex('3 \\oplus b = \\infty')}, since ${tex('\\min(3, b) \\le 3')}.</p>
    <p>Everything works equally well with the maximum in place of the minimum and ${tex('-\\infty')} as zero; negating every number turns one convention into the other.
    <i>6 intro</i> and the 9- and 16-piece puzzles use the minimum; <i>Rev 2</i> and the rational puzzles use the maximum. Try both:</p>
    <div class="calc" data-calc>
      <label>${tex('a')} <input type="number" step="any" value="3" data-calc-a></label>
      <label>${tex('b')} <input type="number" step="any" value="5" data-calc-b></label>
      <div class="segmented" role="group" aria-label="Convention">
        <button type="button" data-calc-mode="min" aria-pressed="true">min</button><button type="button" data-calc-mode="max" aria-pressed="false">max</button>
      </div>
      <output data-calc-out></output>
    </div>`;
}

function bindCalculator(root: HTMLElement): void {
  const box = root.querySelector<HTMLElement>('[data-calc]')!;
  const a = box.querySelector<HTMLInputElement>('[data-calc-a]')!;
  const b = box.querySelector<HTMLInputElement>('[data-calc-b]')!;
  const out = box.querySelector<HTMLOutputElement>('[data-calc-out]')!;
  let mode: Convention = 'min';
  const show = () => {
    const x = Number(a.value), y = Number(b.value);
    if (!Number.isFinite(x) || !Number.isFinite(y) || a.value === '' || b.value === '') {
      out.textContent = 'Enter two numbers.';
      return;
    }
    const sum = mode === 'min' ? Math.min(x, y) : Math.max(x, y);
    const r = (v: number) => num(v, 4);
    out.innerHTML = [
      tex(`${r(x)} \\oplus ${r(y)} = \\${mode}(${r(x)}, ${r(y)}) = ${r(sum)}`),
      tex(`${r(x)} \\odot ${r(y)} = ${r(x)} + ${r(y)} = ${r(x + y)}`),
      tex(`${r(x)} \\oslash ${r(y)} = ${r(x)} - ${r(y)} = ${r(x - y)}`),
    ].map((line) => `<span>${line}</span>`).join('');
  };
  box.querySelectorAll<HTMLButtonElement>('[data-calc-mode]').forEach((button) => button.addEventListener('click', () => {
    mode = button.dataset.calcMode as Convention;
    box.querySelectorAll('[data-calc-mode]').forEach((other) => other.setAttribute('aria-pressed', String(other === button)));
    show();
  }));
  a.addEventListener('input', show);
  b.addEventListener('input', show);
  show();
}

/** F(x) = x² ⊕ 1 ⊙ x ⊕ 4 = min(2x, 1 + x, 4), with tropical roots 1 and 3. */
const ONE_VARIABLE: Term[] = [{ id: 'A', a: 2, b: 0, c: 0 }, { id: 'B', a: 1, b: 0, c: 1 }, { id: 'C', a: 0, b: 0, c: 4 }];

function oneVariableSection(): string {
  const [lo, hi] = [-1, 5];
  const pieces = intervals(ONE_VARIABLE, 'min', lo, hi);
  const breaks = pieces.slice(1).map((p) => p.from);
  const graph = graphSvg({
    lo, hi, fn: (x) => evaluate(ONE_VARIABLE, 'min', x, 0), breaks, band: pieces, lines: ONE_VARIABLE,
    ticks: [-1, 0, 1, 2, 3, 4, 5], yRange: [-3, 6],
    marks: breaks.map((x) => ({ x, label: `x = ${formatNumber(x)}` })),
    title: 'Graph of F(x) = min(2x, 1 + x, 4)',
  });
  const where = (id: string) => {
    const p = pieces.find((q) => q.id === id)!;
    if (p.from === lo) return tex(`x \\le ${num(p.to)}`);
    if (p.to === hi) return tex(`x \\ge ${num(p.from)}`);
    return tex(`${num(p.from)} \\le x \\le ${num(p.to)}`);
  };
  return `
    <h2 id="one-variable">2. Tropical polynomials in one variable</h2>
    <p>Powers are repeated tropical products, ${tex('x^{a} = x \\odot \\cdots \\odot x = a x')}, so a tropical monomial ${tex('c \\odot x^{a}')} is the affine function ${tex('c + a x')}: a line of slope ${tex('a')}.
    A tropical polynomial, a tropical sum of monomials, is therefore a minimum of affine functions:</p>
    ${math('c_0 \\odot x^{a_0} \\oplus \\cdots \\oplus c_n \\odot x^{a_n} = \\min_i\\,(c_i + a_i x).')}
    <p>Its graph follows the lowest line, so it is piecewise linear and concave, with a corner wherever two terms tie for the minimum.
    These corners are the <b>tropical roots</b>. An ordinary polynomial vanishes where its terms cancel, and the tropical analogue of cancelling is a tie. For example:</p>
    <div class="linked" data-link="one">
      ${math(`\\begin{aligned} F(x) &= ${tropical(ONE_VARIABLE)} \\\\ &= ${classical(ONE_VARIABLE, 'min')} \\end{aligned}`)}
      ${figure(graph, 'The bold graph is F and the faint lines are its terms. Hover or tap a term, a line or a strip below the graph.')}
    </div>
    <p>The lowest term is ${tex(affine(0, 2, 0))} for ${where('A')}, ${tex(affine(1, 1, 0))} for ${where('B')} and ${tex('4')} for ${where('C')},
    so the tropical roots are ${breaks.map((x) => tex(`x = ${num(x)}`)).join(' and ')}. As for ordinary polynomials, the roots give a factorisation,
    ${tex('F = (x \\oplus 1) \\odot (x \\oplus 3)')}: expanding gives ${tex('\\min(2x,\\ 1 + x,\\ 3 + x,\\ 4)')},
    and ${tex('3 + x')} always exceeds ${tex('1 + x')}, so it can be dropped.</p>`;
}

function twoVariableSection(d: ReturnType<typeof intro>, name: string): string {
  const regions = regionsSvg(d.cells, { box: d.box, ticks: d.ticks, title: `Regions of the ${name} polynomial` });
  return `
    <h2 id="two-variables">3. Two variables: regions and the tropical curve</h2>
    <p>In two variables, a tropical monomial ${tex('c \\odot x^{a} \\odot y^{b}')} is the affine function ${tex('c + a x + b y')}, whose graph is a plane,
    and a tropical polynomial is a minimum of planes. Here is the polynomial behind <a href="${href('new5')}">${escapeHtml(name)}</a>, in both notations:</p>
    <div class="linked" data-link="intro">
      ${math(tropicalLines('F', d.terms))}
      ${math(classicalLines('F(x, y)', d.terms, d.convention))}
      <div class="fig-row">
        ${figure(regions, `The square ${tex(`[${num(d.box[0])}, ${num(d.box[2])}]^2`)}, split into the regions where each term is smallest.`)}
        ${figure(relief('intro'), 'The graph of F as the assembled relief puzzle. Drag to turn it; click a piece to highlight its term.')}
      </div>
      <p class="readout" data-readout aria-live="polite">Hover or tap a term, a region or a piece.</p>
    </div>
    <p>Each region is convex, being cut out by the inequalities saying that its term is at most each of the others, and over it the graph of F is a flat piece of that term's plane.
    Like a minimum of lines, a minimum of planes is concave, so the graph is a roof whose creases are all ridges.</p>
    <p>The creases lie over the boundaries between regions, where two or more terms tie. Together they form the <b>tropical curve</b> of F:
    straight segments meeting where three or more regions come together. It is the two-variable analogue of the tropical roots,
    and the tropical counterpart of a curve defined by a polynomial equation.</p>`;
}

function puzzleSection(d: ReturnType<typeof intro>, puzzle: TropicalPuzzle): string {
  const s = d.scale;
  const shift = (c: number, v: string) => (c === 0 ? v : `${v} ${c < 0 ? '+' : '-'} ${num(Math.abs(c))}`);
  return `
    <h2 id="puzzles">4. From a function to a puzzle</h2>
    <p>To make a puzzle, take a tropical polynomial and a square: each region becomes a piece, so every piece is convex.
    For ${escapeHtml(puzzle.name)}, the square ${tex(`[${num(d.box[0])}, ${num(d.box[2])}]^2`)} is scaled to a ${formatNumber(2 * d.half * s.mmPerUnit, 0)} mm tray:</p>
    ${math(`X = ${num(s.mmPerUnit, 0)}\\,(${shift(d.center[0], 'x')})\\ \\text{mm}, \\qquad Y = ${num(s.mmPerUnit, 0)}\\,(${shift(d.center[1], 'y')})\\ \\text{mm}.`)}
    <p>In the <b>relief</b> variant, the top of each piece is the graph of F over its region, rescaled to a printable height:</p>
    ${math(`\\text{height}(x, y) = ${num(s.minThicknessMm, 0)} + ${num(s.reliefMm, 0)}\\,\\frac{F(x, y) - F_{\\min}}{F_{\\max} - F_{\\min}}\\ \\text{mm},`)}
    <p>where ${tex('F_{\\min}')} and ${tex('F_{\\max}')} are the extremes of F on the square, so pieces are ${num(s.minThicknessMm, 0)} to ${num(s.minThicknessMm + s.reliefMm, 0)} mm thick.
    Since F is continuous, neighbouring roofs meet all along their shared edges, and a relief puzzle is solved only when the pieces fill the tray
    <i>and</i> their roofs form one continuous surface. In the <b>flat</b> variant all pieces have the same thickness and only the outlines matter.</p>
    <p>Puzzles using the maximum, such as <a href="${href('rev2')}">Rev 2</a>, are the other way up: a maximum of planes is convex, so the graph is a bowl whose creases are all valleys.</p>
    <p class="cta"><a href="${href('new5')}">Play ${escapeHtml(puzzle.name)}</a> or try it <a href="${href('new5-flat')}">flat</a>.</p>`;
}

/** P = max(0, x − 1, y − 1) and Q = max(x, y, 1 + x + y): two tropical lines, not a gallery puzzle. */
const EXAMPLE_P: Term[] = [{ id: 'A', a: 0, b: 0, c: 0 }, { id: 'B', a: 1, b: 0, c: -1 }, { id: 'C', a: 0, b: 1, c: -1 }];
const EXAMPLE_Q: Term[] = [{ id: 'a', a: 1, b: 0, c: 0 }, { id: 'b', a: 0, b: 1, c: 0 }, { id: 'c', a: 1, b: 1, c: 1 }];
const EXAMPLE_HALF = 3;
const EXAMPLE_SCALE: ReliefScale = { mmPerUnit: 24, center: [0, 0], minThicknessMm: 8, reliefMm: 35 };

function rationalExample() {
  const region = square([0, 0], EXAMPLE_HALF);
  const cells = rationalCells(EXAMPLE_P, EXAMPLE_Q, 'max', region);
  const pOutlines = polynomialCells(EXAMPLE_P, 'max', region).map((c) => c.polygon);
  const qOutlines = polynomialCells(EXAMPLE_Q, 'max', region).map((c) => c.polygon);
  return { cells, pOutlines, qOutlines };
}

function rationalSection(): string {
  const { cells, pOutlines, qOutlines } = rationalExample();
  const h = EXAMPLE_HALF;
  const regions = regionsSvg(cells, {
    box: [-h, -h, h, h], ticks: [-h, 0, h], rel: (c) => c.terms,
    overlays: [{ polygons: pOutlines, className: 'valley' }, { polygons: qOutlines, className: 'ridge' }],
    title: 'Cells of the rational example',
  });
  const present = new Set(cells.map((c) => c.id));
  const missing = EXAMPLE_P.flatMap((p) => EXAMPLE_Q.map((q) => p.id + q.id)).filter((id) => !present.has(id));
  // The explanation below is written for these two missing cells.
  if (missing.join() !== 'Bb,Ca') throw new Error(`rational example: missing cells ${missing.join()}`);
  return `
    <h2 id="rational">5. Tropical rational functions</h2>
    <p>A <b>tropical rational function</b> is a tropical quotient of two tropical polynomials, ${tex('F = P \\oslash Q = P - Q')}.
    The rational puzzles use the maximum, so ${tex('P')} is convex and ${tex('-Q')} is concave, and the graph of ${tex('F')} has both kinds of crease:
    <span class="valley-text">valleys</span> along the curve of ${tex('P')} and <span class="ridge-text">ridges</span> along the curve of ${tex('Q')}.</p>
    <p>Overlaying the regions of ${tex('P')} and ${tex('Q')} cuts the square into <b>cells</b>, which become the pieces.
    On each cell one term ${tex('p')} of ${tex('P')} and one term ${tex('q')} of ${tex('Q')} are the largest, so ${tex('F = p - q')} there; we name the cell ${tex('pq')}.
    In this small example, which is not a gallery puzzle, ${tex('P')} and ${tex('Q')} have three terms each, so each curve is three rays from a point:</p>
    <div class="linked" data-link="rational">
      ${math(`\\begin{aligned} P &= ${tropical(EXAMPLE_P)} \\\\ &= ${classical(EXAMPLE_P, 'max', 2, false)} \\end{aligned}`)}
      ${math(`\\begin{aligned} Q &= ${tropical(EXAMPLE_Q)} \\\\ &= ${classical(EXAMPLE_Q, 'max', 2, false)} \\end{aligned}`)}
      <div class="fig-row">
        ${figure(regions, `The cells on ${tex(`[-${h}, ${h}]^2`)}, with <span class="valley-text">P's curve</span> and <span class="ridge-text">Q's curve</span>.`)}
        ${figure(relief('rational'), 'The graph of P − Q as relief pieces. Drag to turn it; click a piece.')}
      </div>
      <p class="readout" data-readout aria-live="polite">Hover or tap a term or a cell.</p>
    </div>
    <p>Of the nine possible cells, only ${words(cells.length)} occur. ${tex('Bb')} would need ${tex('x \\ge 1')}, where ${tex('-1 + x')} is largest in ${tex('P')},
    and ${tex('x \\le -1')}, where ${tex('y')} is largest in ${tex('Q')}; likewise ${tex('Ca')} would need both ${tex('y \\ge 1')} and ${tex('y \\le -1')}.
    The gallery's <a href="${href('rat1')}">11 rational</a> and <a href="${href('rat2')}">20 rational</a> are built the same way from larger ${tex('P')} and ${tex('Q')}.</p>`;
}

/** The 27 corrugated function, split as P = Px(x) ⊙ Py(y) (tests/math.test.ts checks the factoring). */
function corrugated(puzzle: TropicalPuzzle) {
  const t = puzzle.tropical;
  const numerator = parseTerms(t.numerator!);
  const denominator = parseTerms(t.denominator!);
  const half = parseCoefficient(t.domain);
  const region = square([0, 0], half);
  const aValues = [...new Set(numerator.map((p) => p.a))].sort((x, y) => x - y);
  const bValues = [...new Set(numerator.map((p) => p.b))].sort((x, y) => x - y);
  const c = (a: number, b: number) => numerator.find((p) => p.a === a && p.b === b)!.c;
  const [a0, b0] = [aValues[0], bValues[0]];
  const px: Term[] = aValues.map((a) => ({ id: `X${a}`, a, b: 0, c: c(a, b0) - c(a0, b0) }));
  const py: Term[] = bValues.map((b) => ({ id: `Y${b}`, a: b, b: 0, c: c(a0, b) }));
  // Q's terms that depend on x only make the sawtooth; the rest is the extra term.
  const qx = denominator.filter((q) => q.b === 0);
  const extra = denominator.filter((q) => q.b !== 0);
  const pxPieces = intervals(px, 'max', -half, half);
  const qxPieces = intervals(qx, 'max', -half, half);
  const valleys = pxPieces.slice(1).map((p) => p.from);
  const ridges = qxPieces.slice(1).map((q) => q.from);
  const breaks = [...valleys, ...ridges].sort((x, y) => x - y);
  const edges = [-half, ...breaks, half];
  const g = (x: number) => evaluate(px, 'max', x, 0) - evaluate(qx, 'max', x, 0);
  const faces = edges.slice(0, -1).map((from, i) => {
    const mid = (from + edges[i + 1]) / 2;
    const xTerm = pxPieces.find((p) => mid >= p.from && mid <= p.to)!.id;
    const qTerm = qxPieces.find((q) => mid >= q.from && mid <= q.to)!.id;
    return { id: `${i + 1}`, from, to: edges[i + 1], rel: [xTerm, qTerm], label: `${i + 1}` };
  });
  const cells = rationalCells(numerator, denominator, t.convention, region);
  const cellRel = (cell: Cell): string[] => {
    const p = numerator.find((n) => n.id === cell.terms[0])!;
    const q = cell.terms[1];
    const face = faces.find((f) => f.rel[0] === `X${p.a}` && f.rel[1] === q);
    return [...cell.terms, `X${p.a}`, `Y${p.b}`, ...(face ? [face.id] : [])];
  };
  const scale: ReliefScale = {
    mmPerUnit: parseCoefficient(t.xyMmPerUnit), center: [0, 0],
    minThicknessMm: puzzle.geometry.minThicknessMm ?? 8, reliefMm: puzzle.geometry.reliefMm ?? 35,
  };
  return { numerator, denominator, half, region, px, py, qx, extra, valleys, ridges, breaks, g, faces, cells, cellRel, scale };
}

function corrugatedSection(puzzle: TropicalPuzzle): string {
  const d = corrugated(puzzle);
  const h = d.half;
  const valleyHeights = d.valleys.map(d.g);
  const ridgeHeights = d.ridges.map(d.g);
  const sawtooth = graphSvg({
    lo: -h, hi: h, fn: d.g, breaks: d.breaks, ticks: [-h, 0, h],
    band: d.faces.map((f) => ({ id: f.id, from: f.from, to: f.to, rel: f.rel })),
    marks: [...d.valleys.map((x) => ({ x, label: 'valley', className: 'valley' })), ...d.ridges.map((x) => ({ x, label: 'ridge', className: 'ridge' }))],
    title: 'The sawtooth Px(x) − Qx(x)',
  });
  const hPieces = intervals(d.py, 'max', -h, h);
  const hGraph = graphSvg({
    lo: -h, hi: h, fn: (y) => evaluate(d.py, 'max', y, 0), breaks: hPieces.slice(1).map((p) => p.from), ticks: [-h, 0, h], variable: 'y',
    band: hPieces.map((p) => ({ ...p })), title: 'The convex function Py(y)',
  });
  const regions = regionsSvg(d.cells, {
    box: [-h, -h, h, h], ticks: [-h, 0, h], rel: d.cellRel, labelSize: 9,
    overlays: [
      { polygons: polynomialCells(d.numerator, 'max', d.region).map((c) => c.polygon), className: 'valley' },
      { polygons: polynomialCells(d.denominator, 'max', d.region).map((c) => c.polygon), className: 'ridge' },
    ],
    title: 'Cells of 27 corrugated',
  });
  const spread = (values: number[]) => Math.max(...values) - Math.min(...values) < 1e-6;
  const list = (ids: string[]) => ids.length > 1 ? `${ids.slice(0, -1).join(', ')} and ${ids.at(-1)}` : ids[0];
  const qxNames = list(d.qx.map((q) => tex(q.id)));
  const wedge = d.cells.filter((c) => d.extra.some((q) => c.terms[1] === q.id)).map((c) => tex(c.id));
  const same = spread(valleyHeights) && spread(ridgeHeights);
  return `
    <p>In a relief puzzle the roofs usually help a lot, by showing which pieces belong together. <a href="${href('cor1')}">${escapeHtml(puzzle.name)}</a> is a rational puzzle
    designed so that they help as little as possible. It is ${tex('F = P \\oslash Q')} on ${tex(`[-${h}, ${h}]^2`)}, where ${tex('Q')} has ${words(d.denominator.length)} terms
    and ${tex('P')} is the tropical <i>product</i> of a polynomial in ${tex('x')} with ${words(d.px.length)} terms and one in ${tex('y')} with ${words(d.py.length)}
    (coefficients rounded to two decimals; the puzzle's recipe has the exact fractions):</p>
    <div class="linked" data-link="corrugated">
      ${math('P = P_x(x) \\odot P_y(y),')}
      ${math(extremumLines('P_x', d.px.map((p) => link(p.id, affine(p.c, p.a, 0))), 'max', ',', 3))}
      ${math(extremumLines('P_y', d.py.map((p) => link(p.id, affine(p.c, p.a, 0, ['y', 'y']))), 'max', ',', 3))}
      ${math(extremumLines('Q', d.denominator.map((q) => named(q.id, affine(q.c, q.a, q.b))), 'max', '.'))}
      <p>So ${tex('P(x, y) = P_x(x) + P_y(y)')}. Three of the four terms of ${tex('Q')}, ${qxNames}, do not involve ${tex('y')}; let ${tex('Q_x(x)')} be their maximum.
      Everywhere except where ${tex(d.extra[0].id)} is the largest term of ${tex('Q')}, we have ${tex('Q = Q_x(x)')}, and so</p>
      ${math('F(x, y) = \\bigl(P_x(x) - Q_x(x)\\bigr) + P_y(y),')}
      <p>a function of ${tex('x')} plus a function of ${tex('y')}. The pieces line up in columns, separated by the tropical roots of ${tex('P_x')} and ${tex('Q_x')},
      and in rows, separated by those of ${tex('P_y')}. Every left-to-right cut through the roof has the same profile ${tex('P_x - Q_x')}, shifted up or down by ${tex('P_y(y)')}, like corrugated metal.</p>
      <div class="spoiler" data-spoiler>
        <div class="spoiler-cover">
          <p>These figures show how ${escapeHtml(puzzle.name)} fits together.</p>
          <button type="button" data-spoiler-show>Show the figures (this reveals the solution)</button>
        </div>
        <div class="spoiler-body" hidden>
          <div class="fig-row">
            ${figure(sawtooth, `${tex('P_x(x) - Q_x(x)')}: a sawtooth with one face for each of the ${words(d.faces.length)} columns. The corners of ${tex('P_x')} are <span class="valley-text">valleys</span> and the corners of ${tex('Q_x')} are <span class="ridge-text">ridges</span>.`)}
            ${figure(hGraph, `${tex('P_y(y)')}: convex, with one face for each of the ${words(hPieces.length)} rows.`)}
          </div>
          <div class="fig-row">
            ${figure(regions, `The ${d.cells.length} cells. Click a term above to see its columns, rows or wedge.`)}
            ${figure(relief('corrugated'), 'The corrugated roof. Drag to turn it; click a piece.')}
          </div>
          <p class="readout" data-readout aria-live="polite">Hover or tap a term, a column of the sawtooth, a row or a cell.</p>
        </div>
      </div>
    </div>
    <p>This is what makes the puzzle hard. The sawtooth's ${words(d.valleys.length)} valleys are at ${same ? '' : 'nearly '}the same height, and so are its ${words(d.ridges.length)} ridges,
    so the roof has the same profile, ${tex('P_y(y)')} plus a constant, along every valley line, and likewise along every ridge line.
    Matching roofs therefore cannot tell you which column goes next to which. No two pieces have the same shape, but whole columns can trade places:
    without ${tex(d.extra[0].id)}, there would be 12 ways to fill the tray with all roofs matching.</p>
    <p>The term ${tex(`${d.extra[0].id} = ${affine(d.extra[0].c, d.extra[0].a, d.extra[0].b)}`)}, the only term of ${tex('Q')} involving ${tex('y')},
    is largest only in a small wedge along one wall of the tray, made of the cells ${wedge.join(' and ')}. It changes the shapes of the pieces around it,
    which breaks the symmetry: with the wedge, the only way to fill the tray with matching roofs is the original one.</p>`;
}

function content(introPuzzle: TropicalPuzzle, corrugatedPuzzle: TropicalPuzzle): string {
  const d = intro(introPuzzle);
  return `
    <p>Here we introduce the mathematics behind the puzzles: tropical arithmetic, tropical polynomials and their graphs,
    how a polynomial becomes a puzzle, and tropical rational functions, ending with the 27 corrugated puzzle.</p>
    <p class="spoiler-note">This page shows the solution to ${escapeHtml(introPuzzle.name)}, so you may want to <a href="${href('new5')}">solve it first</a>.
    The figures for 27 corrugated stay covered until you open them.</p>
    ${arithmeticSection()}
    ${oneVariableSection()}
    ${twoVariableSection(d, introPuzzle.name)}
    ${puzzleSection(d, introPuzzle)}
    ${rationalSection()}
    ${corrugatedSection(corrugatedPuzzle)}`;
}

// ---------------------------------------------------------------- interaction

/** Wire one linked example: highlighting, the readout line and (optionally) its 3D view. */
function bindExample(
  root: HTMLElement, name: string, cells: Cell[] | null, scale: ReliefScale | null,
  describe: (active: string | null) => string, rel: (cell: Cell) => string[] = (c) => c.terms.filter((t) => t !== c.id),
): Linker {
  const box = root.querySelector<HTMLElement>(`[data-link="${name}"]`)!;
  const linker = new Linker(box);
  const readout = box.querySelector<HTMLElement>('[data-readout]');
  let view: ReturnType<typeof createRelief> = null;
  const slot = box.querySelector<HTMLElement>(`[data-relief="${name}"]`);
  if (cells && scale && slot) {
    cells.forEach((c) => linker.register(c.id, rel(c)));
    view = createRelief(slot, cells, scale, (id) => linker.toggle(id));
  }
  linker.listen((lit, active) => {
    view?.setLit(lit);
    if (readout) readout.innerHTML = describe(active);
  });
  return linker;
}

function cellDescription(cell: Cell, prefix: string): string {
  return `${prefix} ${tex(cell.id)}: ${tex(`F = ${affine(cell.f.c, cell.f.a, cell.f.b)}`)}`;
}

function bindAll(root: HTMLElement, introPuzzle: TropicalPuzzle, corrugatedPuzzle: TropicalPuzzle): void {
  bindCalculator(root);
  const d = intro(introPuzzle);
  new Linker(root.querySelector<HTMLElement>('[data-link="one"]')!);
  bindExample(root, 'intro', d.cells, d.scale, (active) => {
    const cell = d.cells.find((c) => c.id === active);
    return cell
      ? `${cellDescription(cell, 'Region and piece')}. The roof of this piece is part of that plane, rescaled.`
      : 'Hover or tap a term, a region or a piece.';
  });

  const example = rationalExample();
  bindExample(root, 'rational', example.cells, EXAMPLE_SCALE, (active) => {
    const cell = example.cells.find((c) => c.id === active);
    if (cell) {
      const p = EXAMPLE_P.find((t) => t.id === cell.terms[0])!;
      const q = EXAMPLE_Q.find((t) => t.id === cell.terms[1])!;
      return `Cell ${tex(cell.id)}: ${tex(`F = (${affine(p.c, p.a, p.b)}) - (${affine(q.c, q.a, q.b)}) = ${affine(cell.f.c, cell.f.a, cell.f.b)}`)}`;
    }
    const term = [...EXAMPLE_P, ...EXAMPLE_Q].find((t) => t.id === active);
    if (!term) return 'Hover or tap a term or a cell.';
    const owner = EXAMPLE_P.includes(term) ? 'P' : 'Q';
    const where = example.cells.filter((c) => c.terms.includes(term.id)).map((c) => tex(c.id));
    return `${tex(affine(term.c, term.a, term.b))} is the largest term of ${tex(owner)} on the cells ${where.join(', ')}.`;
  });

  const spoiler = root.querySelector<HTMLElement>('[data-spoiler]')!;
  spoiler.querySelector('[data-spoiler-show]')!.addEventListener('click', () => {
    spoiler.querySelector<HTMLElement>('.spoiler-cover')!.hidden = true;
    spoiler.querySelector<HTMLElement>('.spoiler-body')!.hidden = false;
    const c = corrugated(corrugatedPuzzle);
    bindExample(root, 'corrugated', c.cells, c.scale, (active) => {
      const cell = c.cells.find((x) => x.id === active);
      if (cell) return cellDescription(cell, 'Piece');
      const face = c.faces.find((f) => f.id === active);
      if (face) {
        const p = c.px.find((t) => t.id === face.rel[0])!;
        const q = c.denominator.find((t) => t.id === face.rel[1])!;
        return `Column ${face.label}: here ${tex(affine(p.c, p.a, 0))} is the largest term of ${tex('P_x')} and ${tex(affine(q.c, q.a, q.b))} the largest of ${tex('Q_x')}.`;
      }
      const px = c.px.find((t) => t.id === active);
      if (px) return `Where ${tex(affine(px.c, px.a, 0))} is the largest term of ${tex('P_x')}.`;
      const py = c.py.find((t) => t.id === active);
      if (py) return `A row: where ${tex(affine(py.c, py.a, 0, ['y', 'y']))} is the largest term of ${tex('P_y')}.`;
      const q = c.denominator.find((t) => t.id === active);
      if (q) {
        return c.extra.includes(q)
          ? `The wedge where ${tex(affine(q.c, q.a, q.b))}, the term ${tex(q.id)} of ${tex('Q')}, is the largest.`
          : `Where ${tex(affine(q.c, q.a, q.b))} is the largest term of ${tex('Q')}.`;
      }
      return 'Hover or tap a term, a column of the sawtooth, a row or a cell.';
    }, c.cellRel);
  }, { once: true });
}

export async function renderMathPage(root: HTMLElement): Promise<void> {
  document.title = 'The mathematics · Tropical Puzzle Lab';
  root.innerHTML = `
    <div class="gallery doc math">
      <a class="back" href="${base}">← Gallery</a>
      <header class="intro"><h1>The mathematics behind the puzzles</h1></header>
      <div data-doc><p class="loading">Loading…</p></div>
    </div>`;
  const doc = root.querySelector<HTMLElement>('[data-doc]')!;
  try {
    const [introPuzzle, corrugatedPuzzle] = await Promise.all([fetchPuzzle('new5'), fetchPuzzle('cor1')]);
    doc.innerHTML = content(introPuzzle, corrugatedPuzzle);
    bindAll(doc, introPuzzle, corrugatedPuzzle);
    // The page is built after load, so jump to a #section link by hand.
    if (window.location.hash) document.getElementById(window.location.hash.slice(1))?.scrollIntoView();
  } catch (error) {
    doc.innerHTML = `<p class="error">Could not load the examples (${escapeHtml(String(error))}).</p>`;
  }
}

