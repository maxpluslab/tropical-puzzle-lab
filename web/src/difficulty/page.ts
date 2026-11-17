// Explanation of the difficulty rating (search effort) and the secondary diversity statistic. Every parameter shown here is read from the `difficulty`
// block of index.json, which tpl-export copies from the generator's configuration, so the page
// cannot drift from the implementation.
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { escapeHtml } from '../player/player';
import type { DifficultyConfig, PuzzleIndex } from '../types';
import { assemblies, fetchIndex, pips } from './rating';
import { footerHtml } from '../footer';

const base = import.meta.env.BASE_URL;

const tex = (source: string, displayMode = false): string => katex.renderToString(source, { displayMode, throwOnError: false });
const math = (source: string): string => tex(source, true);

/** The diversity formula for uniform weights at the configured order, and what it means. */
function orderSection(q: DifficultyConfig['diversity']['q']): string {
  if (q === 'infinity') {
    return `<p>We use ${tex('q = \\infty')} with uniform weights ${tex('p_i = 1/n')}:</p>
      ${math('D = {}^{\\infty}\\!D^{Z} = \\frac{n}{\\max_i \\sum_j Z_{ij}}.')}
      <p>This is the most conservative order: it is set by the piece with the most look-alikes.</p>`;
  }
  if (q === 2) {
    return `<p>We use ${tex('q = 2')} with uniform weights ${tex('p_i = 1/n')}:</p>
      ${math('D = {}^{2}\\!D^{Z} = \\frac{n^2}{\\sum_i \\sum_j Z_{ij}},')}
      <p>the reciprocal of the mean similarity between two pieces drawn at random (with replacement). It weighs every pair equally,
      so it is less dominated by the single most crowded piece than ${tex('q = \\infty')}.</p>`;
  }
  if (q === 1) {
    return `<p>We use ${tex('q = 1')} (the limit) with uniform weights ${tex('p_i = 1/n')}:</p>
      ${math('D = {}^{1}\\!D^{Z} = \\exp\\Bigl(-\\frac1n \\sum_i \\log \\frac1n \\sum_j Z_{ij}\\Bigr).')}`;
  }
  return `<p>We use ${tex(`q = ${q}`)} with uniform weights ${tex('p_i = 1/n')}:</p>
    ${math(`D = {}^{${q}}\\!D^{Z} = \\Bigl(\\frac1n \\sum_i \\Bigl(\\frac1n \\sum_j Z_{ij}\\Bigr)^{${q} - 1}\\Bigr)^{\\frac{1}{1-${q}}}.`)}`;
}

/** Nodes as a reader counts them: 1 529, 1.06 million; a lower bound gets "≥". */
export function formatNodes(nodes: number, exhaustive: boolean): string {
  const text = nodes >= 1e6 ? `${(nodes / 1e6).toFixed(2).replace(/\.?0+$/, '')} million` : nodes.toLocaleString('en-GB').replace(/,/g, '\u2009');
  return exhaustive ? text : `≥ ${text}`;
}

/** One row per rating: the node interval that maps to it. */
function mappingRows(config: DifficultyConfig): string {
  const cuts = config.thresholds;
  return [0, 1, 2, 3, 4]
    .map((k) => {
      const lower = k === 0 ? '' : `10^{${cuts[k - 1]}} \\le `;
      const upper = k === 4 ? '' : ` < 10^{${cuts[k]}}`;
      return `<tr><td>${pips(k + 1)} ${k + 1}</td><td>${tex(`${lower}\\text{nodes}${upper}`)}</td></tr>`;
    })
    .join('');
}

function puzzleRows(index: PuzzleIndex): string {
  return index.puzzles
    .map((e) => `<tr>
      <td><a href="${base}?puzzle=${encodeURIComponent(e.id)}">${escapeHtml(e.code)}</a></td>
      <td>${e.variant === 'relief' ? 'relief' : 'flat tiling'}</td>
      <td class="num">${e.pieceCount}</td>
      <td class="num">${formatNodes(e.difficulty.nodes, e.difficulty.exhaustive)}</td>
      <td class="num">${assemblies(e.difficulty)}</td>
      <td>${pips(e.difficulty.rating)} ${e.difficulty.rating}</td>
      <td class="num">${e.difficulty.diversity.toFixed(2)}</td>
    </tr>`)
    .join('');
}

function content(index: PuzzleIndex): string {
  const c = index.difficulty;
  const solver = c.solver;
  const limit = formatNodes(solver.nodeLimit, true);
  return `
    <p>Every puzzle gets a rating from 1 (easiest) to 5 (hardest): <b>how much a computer search has to try</b> before it has
    found every assembly it can find. It is an experimental heuristic, not a validated measure of how hard you will find the puzzle.</p>
    <div class="callout">
      <p><b>What the rating is, and what it is not</b></p>
      <ul>
        <li><b>Search effort.</b> The rating is the number of placements the search tries (nodes), on a logarithmic scale. Nothing else goes into it.</li>
        <li><b>Candidate placements.</b> The search only tries placements of one kind: a piece corner in a corner of the empty space, with an edge
        flush against it (in relief, with the roofs continuing). For exactly fitting convex pieces this kind is known to include every assembly,
        but the search computes in floating point and leaves out assemblies that fit only within the player's tolerances.
        So &ldquo;every assembly&rdquo; and &ldquo;one solution&rdquo; on this site mean every assembly <i>among these placements</i>,
        counted once up to turning the whole tray. It is computational evidence, not a proof of uniqueness.</li>
        <li><b>Lower bounds.</b> The search stops at ${limit} nodes. A puzzle it has not finished by then gets a rating that is only a floor,
        node and solution counts marked ≥, and &ldquo;?&rdquo; for the count when it found none.</li>
        <li><b>Human difficulty.</b> Not measured. Nobody has yet timed people solving these puzzles, and a search that finds a
        puzzle easy may not be how a person sees it.</li>
      </ul>
    </div>

    <h2>1. The search</h2>
    <p>The search is <code>${escapeHtml(solver.id)}</code> from
    <a href="${escapeHtml(solver.repository)}" target="_blank" rel="noopener">tiling-solvers</a>, our companion project for solving
    these puzzles by computer. It gets each puzzle the way you do: the tray and the pieces, turned, shuffled and renamed, with no hint
    of the solution. It places pieces one at a time, each against the corner of the empty space, trying every piece and every way
    it can touch what is already there, and backs up when a piece cannot go anywhere.</p>
    <ul>
      <li><b>Relief puzzles</b> are searched with their roofs: two pieces may only touch where their tops meet at the same height.</li>
      <li><b>Flat puzzles</b> are searched with footprints only.</li>
    </ul>
    <p>When the search runs to its end, it has found every assembly among the placements it considers (see above) and shown there is
    no other among them. A <i>node</i> is one placement it tries. It stops at ${limit} nodes; a puzzle it has not finished by then gets
    a lower bound, marked ≥. The details of what a result claims are in tiling-solvers'
    <a href="${escapeHtml(solver.repository)}/blob/main/docs/solver-contract.md" target="_blank" rel="noopener">solver contract</a>.</p>

    <h2>2. From nodes to a rating</h2>
    <p>Effort grows by factors, so the rating uses the logarithm ${tex('x = \\log_{10}(\\text{nodes})')}, cut at
    ${c.thresholds.join(', ')}. Relief and flat puzzles share one scale, so the same rating means the same effort on both.</p>
    <div class="table-wrap"><table class="data">
      <thead><tr><th>Rating</th><th>Search</th></tr></thead>
      <tbody>${mappingRows(c)}</tbody>
    </table></div>
    <p><b>Why relief puzzles rate low.</b> The roofs give most of the matching away. Of the dozens of edges a piece edge could lie
    against by shape, only a handful also continue the surface, so the search makes few wrong turns.
    This is the same wall matching you do by eye. Without the roofs, the flat version of the same pieces can take hundreds of
    thousands of tries.</p>
    <p><b>Many solutions.</b> The rating counts the effort to find <i>every</i> assembly, so a puzzle with very many of them can rate
    high and still be easy to finish: any one of its solutions completes it. The flat Pleat puzzles are the extreme case. Their
    triangles fit together in tens of thousands of ways, so the search stops at its limit while still finding more, and they rate 5.
    In relief, the search runs to its end on the same pieces and finds just one assembly. The gallery and the puzzle page show the number
    of solutions the search found whenever there is more than one; it has a ≥ when the search stopped before it could count them all.</p>

    <h2>Ratings of the current puzzles</h2>
    <p>Assemblies are those the search found, counted up to turning the tray. Diversity is explained below.</p>
    <div class="table-wrap"><table class="data">
      <thead><tr><th>Puzzle</th><th>Variant</th><th class="num">Pieces</th><th class="num">Nodes</th><th class="num">Assemblies</th><th>Rating</th><th class="num">${tex('D')}</th></tr></thead>
      <tbody>${puzzleRows(index)}</tbody>
    </table></div>
    <p class="note">Search counts: ${escapeHtml(solver.id)} ${escapeHtml(solver.version)},
    tiling-solvers commit <code>${escapeHtml(solver.commit.slice(0, 7))}</code>.</p>

    <h2>Shape diversity (not part of the rating)</h2>
    <p>Earlier versions of the gallery rated puzzles by shape diversity: how many genuinely different pieces a puzzle has.
    We still show it as ${tex('D')}, the <i>effective number of distinct pieces</i>, but it does not affect the rating.
    It describes how alike the pieces look, not how hard they are to place.</p>
    <p>Each piece is taken as the solid the player draws: its footprint polygon extruded from the table up to its
    sloped roof (relief puzzles) or to a uniform thickness (flat puzzles). Every such piece is a convex polyhedron.</p>

    <h3>Intrinsic volumes</h3>
    <p>A convex body ${tex('K \\subset \\mathbb{R}^3')} has four intrinsic volumes ${tex('V_0, \\dots, V_3')}, the coefficients
    of the Steiner formula for the volume of its ${tex('\\varepsilon')}-neighbourhood:</p>
    ${math('\\operatorname{vol}(K + \\varepsilon B) = \\sum_{j=0}^{3} \\omega_{3-j}\\, V_j(K)\\, \\varepsilon^{3-j},')}
    <p>where ${tex('\\omega_k')} is the volume of the unit ball in ${tex('\\mathbb{R}^k')}. For a convex polyhedron ${tex('P')} they are</p>
    ${math('V_0(P) = 1, \\qquad V_1(P) = \\frac{1}{2\\pi} \\sum_{e} \\ell_e\\,(\\pi - \\theta_e), \\qquad V_2(P) = \\tfrac12\\,\\operatorname{area}(\\partial P), \\qquad V_3(P) = \\operatorname{vol}(P),')}
    <p>where the sum runs over the edges ${tex('e')}, with length ${tex('\\ell_e')} and interior dihedral angle ${tex('\\theta_e')}.
    ${tex('V_1')} is twice the mean width. A unit cube has ${tex('(V_0, V_1, V_2, V_3) = (1, 3, 3, 1)')}.</p>
    <p><b>Why these?</b> Hadwiger's theorem says every continuous, rigid-motion-invariant valuation on convex bodies is a linear combination
    of ${tex('V_0, \\dots, V_3')}, so they are a complete set of additive, position-independent shape measurements.</p>

    <h3>Removing scale</h3>
    <p>${tex('V_j')} has units of length${tex('^j')}, so we take ${tex('j')}-th roots and divide by a length for the whole puzzle,
    ${tex('L = \\bigl(\\sum_i V_3(P_i)\\bigr)^{1/3}')}:</p>
    ${math('d(P) = \\Bigl(V_0(P),\\ \\frac{V_1(P)}{L},\\ \\frac{V_2(P)^{1/2}}{L},\\ \\frac{V_3(P)^{1/3}}{L}\\Bigr) \\in \\mathbb{R}^4.')}
    <p>Scaling the whole puzzle leaves every ${tex('d(P_i)')} unchanged, and moving a piece rigidly does not change its vector.
    (${tex('V_0')} is the same for every piece, so it never affects distances.)</p>

    <h3>Distance and similarity</h3>
    ${math(`d_{ij} = \\lVert d(P_i) - d(P_j) \\rVert_2, \\qquad Z_{ij} = e^{-u\\, d_{ij}}, \\qquad u = ${c.diversity.u}.`)}
    <p>${tex('Z_{ii} = 1')}, and ${tex('Z_{ij} \\to 0')} as two pieces become very different. Larger ${tex('u')} means only near-identical pieces count as similar.</p>

    <h3>Leinster–Cobbold diversity</h3>
    <p>For a probability distribution ${tex('p')} on the pieces and a similarity matrix ${tex('Z')}, the Leinster–Cobbold diversity of order ${tex('q')} is</p>
    ${math('{}^{q}\\!D^{Z}(p) = \\Bigl(\\sum_{i} p_i\\, (Zp)_i^{\\,q-1}\\Bigr)^{\\frac{1}{1-q}},')}
    <p>with the limits ${tex('{}^{1}\\!D^{Z}(p) = \\exp\\bigl(-\\sum_i p_i \\log (Zp)_i\\bigr)')} and
    ${tex('{}^{\\infty}\\!D^{Z}(p) = 1 / \\max_{i:\\,p_i>0} (Zp)_i')}. It is non-increasing in ${tex('q')}:
    small ${tex('q')} counts rare pieces fully, large ${tex('q')} pays attention mainly to the most common kind.</p>
    ${orderSection(c.diversity.q)}
    <p>In every case ${tex('1 \\le D \\le n')}, and ${tex('D')} is the <i>effective number of distinct pieces</i>: it is 1 when all pieces are
    identical and ${tex('n')} when they are all completely dissimilar (${tex('Z = I')}).</p>`;
}

export async function renderDifficultyPage(root: HTMLElement): Promise<void> {
  document.title = 'Difficulty rating · Tropical Puzzle Lab';
  root.innerHTML = `
    <div class="gallery doc">
      <a class="back" href="${base}">← Gallery</a>
      <header class="intro"><h1>How difficulty is rated</h1></header>
      <div data-doc><p class="loading">Loading…</p></div>
      ${footerHtml()}
    </div>`;
  const doc = root.querySelector<HTMLElement>('[data-doc]')!;
  try {
    doc.innerHTML = content(await fetchIndex());
  } catch (error) {
    doc.innerHTML = `<p class="error">Could not load the ratings (${escapeHtml(String(error))}).</p>`;
  }
}
