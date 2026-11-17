// Mirrors docs/puzzle-format.md (formatVersion 1).

export type Vec2 = [number, number];

export interface Roof {
  /** Height above the underside at the piece origin, mm. */
  z0: number;
  gx: number;
  gy: number;
}

export interface PieceDef {
  id: string;
  /** Convex, counter-clockwise, in mm relative to the piece origin. */
  polygon: Vec2[];
  roof?: Roof;
  thickness?: number;
}

export interface Pose {
  id: string;
  x: number;
  y: number;
  /** Counter-clockwise rotation about the vertical axis, radians. */
  theta: number;
}

export interface Validation {
  contactNoise: number;
  overlapDepth: number;
  outsideDepth: number;
  areaError: number;
  roofMismatch?: number;
  edgeAngleDeg: number;
  edgeMinOverlap: number;
}

export type Variant = 'relief' | 'tiling';

export interface Puzzle {
  formatVersion: 1;
  id: string;
  revision: number;
  /** Construction name shared by both variants, e.g. `Hill 16b`. */
  name: string;
  /** This variant's code, e.g. `Hill 16b-r` (relief) or `Hill 16b-f` (flat). */
  code: string;
  /** Published print listing on Printables, when there is one. */
  printables?: string;
  /** The gallery's "Start here" puzzle; see PuzzleIndexEntry. */
  starter?: boolean;
  description: string;
  variant: Variant;
  geometry: {
    model: 'planar';
    units: 'mm';
    spanMm: number;
    target: { type: 'polygon'; vertices: Vec2[] };
    reliefMm?: number;
    minThicknessMm?: number;
    trayRimMm: number;
  };
  pieces: PieceDef[];
  reference: { poses: Pose[] };
  rules: { translate: boolean; rotate: 'continuous-z'; flip: boolean; snap: boolean };
  validation: Validation;
  scramble: { algorithm: 'v1'; defaultSeed: number };
  provenance: Record<string, unknown>;
  geometryHash: string;
}

export interface PuzzleIndexEntry {
  id: string;
  /** Recipe id; the variants of one construction share footprints and are shown as modes of one puzzle. */
  construction: string;
  revision: number;
  /** Construction name shared by both variants, e.g. `Hill 16b`. */
  name: string;
  /** This variant's code, e.g. `Hill 16b-r` (relief) or `Hill 16b-f` (flat). */
  code: string;
  /** Published print listing on Printables, when there is one. */
  printables?: string;
  /** The gallery's "Start here" puzzle (at most one variant, set in its recipe). */
  starter?: boolean;
  description: string;
  variant: Variant;
  pieceCount: number;
  path: string;
  difficulty: DifficultyRating;
}

/** Precomputed by the generator (`tropical_puzzle_lab/difficulty.py`) from tiling-solvers search counts. */
export interface DifficultyRating {
  /** 1 (easiest) to 5 (hardest). */
  rating: number;
  /** log10(nodes). */
  x: number;
  /** Placements the search tried; a lower bound when `exhaustive` is false. */
  nodes: number;
  /** The search ran to its end (otherwise it stopped at the node limit). */
  exhaustive: boolean;
  /** Assemblies the search found, up to turning the tray. */
  solutions: number;
  /** Secondary statistic: Leinster–Cobbold diversity D of the pieces, in [1, n]. */
  diversity: number;
}

/** The rating parameters, copied from the generator's single configuration block. */
export interface DifficultyConfig {
  method: string;
  solver: { id: string; version: string; repository: string; commit: string; nodeLimit: number };
  /** Four increasing cut points on x = log10(nodes). */
  thresholds: number[];
  /** The secondary statistic's parameters. */
  diversity: {
    method: string;
    u: number;
    /** Order of the Leinster–Cobbold diversity. */
    q: number | 'infinity';
  };
}

export interface PuzzleIndex {
  formatVersion: 1;
  difficulty: DifficultyConfig;
  puzzles: PuzzleIndexEntry[];
}
