import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { printPageHtml, published } from '../src/print/page';
import type { PuzzleIndex } from '../src/types';

const index: PuzzleIndex = JSON.parse(readFileSync(resolve(__dirname, '../../puzzles/index.json'), 'utf8'));

describe('print page', () => {
  it('lists exactly the variants with a Printables listing', () => {
    const ids = published(index).map((e) => e.id);
    expect(ids).toEqual(index.puzzles.filter((e) => e.printables).map((e) => e.id));
    expect(ids).toEqual(expect.arrayContaining(['new2', 'rat2']));
    expect(ids).not.toContain('new2-flat');
  });

  it('links every listing and gives a command for every variant', () => {
    const html = printPageHtml(index);
    for (const e of published(index)) expect(html).toContain(`href="${e.printables}"`);
    for (const e of index.puzzles) expect(html).toContain(`<code>tpl-stl ${e.id}</code>`);
  });

  it('keeps the Windows path intact', () => {
    expect(printPageHtml(index)).toContain('.venv\\Scripts\\activate');
  });
});
