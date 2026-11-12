// Linked highlighting within one example. Every element with data-id is linkable: hovering or
// focusing it previews, clicking pins it (click again to unpin). The highlighted set is the active
// id, the ids it belongs to (its data-rel), and every element that belongs to it.
export type LinkListener = (lit: Set<string>, active: string | null) => void;

export class Linker {
  private hover: string | null = null;
  private pinned: string | null = null;
  private readonly rel = new Map<string, Set<string>>();
  private readonly listeners: LinkListener[] = [];

  constructor(private readonly root: HTMLElement) {
    root.querySelectorAll<HTMLElement | SVGElement>('[data-id]').forEach((el) => this.register(el.dataset.id!, (el.dataset.rel ?? '').split(' ').filter(Boolean)));
    root.querySelectorAll<HTMLElement>('.katex [data-id]').forEach((el) => {
      el.classList.add('term');
      el.tabIndex = 0;
      el.setAttribute('role', 'button');
      el.setAttribute('aria-pressed', 'false');
    });
    const target = (event: Event) => (event.target as Element).closest?.<HTMLElement>('[data-id]') ?? null;
    root.addEventListener('pointerover', (e) => this.setHover(target(e)?.dataset.id ?? null));
    root.addEventListener('pointerleave', () => this.setHover(null));
    // Keyboard focus previews like hover; focus from a click or tap does not, or a tap could never unpin.
    root.addEventListener('focusin', (e) => {
      const el = target(e);
      if (el?.matches(':focus-visible')) this.setHover(el.dataset.id ?? null);
    });
    root.addEventListener('focusout', () => this.setHover(null));
    root.addEventListener('click', (e) => {
      const id = target(e)?.dataset.id;
      if (id) this.toggle(id);
    });
    root.addEventListener('keydown', (e) => {
      const id = target(e)?.dataset.id;
      if (id && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        this.toggle(id);
      }
    });
  }

  /** Make an id linkable without a DOM element (the 3D view's cells). */
  register(id: string, belongsTo: string[]): void {
    const set = this.rel.get(id) ?? new Set<string>();
    belongsTo.forEach((r) => set.add(r));
    this.rel.set(id, set);
  }

  listen(listener: LinkListener): void {
    this.listeners.push(listener);
  }

  toggle(id: string): void {
    this.pinned = this.pinned === id ? null : id;
    this.update();
  }

  private setHover(id: string | null): void {
    if (id === this.hover) return;
    this.hover = id;
    this.update();
  }

  private litFor(active: string | null): Set<string> {
    const lit = new Set<string>();
    if (!active) return lit;
    lit.add(active);
    this.rel.get(active)?.forEach((r) => lit.add(r));
    for (const [id, belongsTo] of this.rel) if (belongsTo.has(active)) lit.add(id);
    return lit;
  }

  private update(): void {
    const active = this.hover ?? this.pinned;
    const lit = this.litFor(active);
    this.root.querySelectorAll<HTMLElement | SVGElement>('[data-id]').forEach((el) => {
      const id = el.dataset.id!;
      el.classList.toggle('lit', lit.has(id));
      el.classList.toggle('pinned', id === this.pinned);
      if (el.getAttribute('role') === 'button') el.setAttribute('aria-pressed', String(id === this.pinned));
    });
    this.listeners.forEach((listener) => listener(lit, active));
  }
}
