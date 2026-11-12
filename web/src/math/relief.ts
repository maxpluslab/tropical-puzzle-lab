// The graph of a piecewise-affine function as assembled relief pieces: each cell is a block whose
// top is the function's plane, scaled the way tpl-export scales a puzzle's roof. Drag to turn it.
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { pieceGeometry, palette } from '../player/meshes';
import type { PieceDef, Vec2 } from '../types';
import { range, type Cell } from './tropical';

export interface ReliefScale {
  /** Domain units to mm, and the domain point placed at the origin. */
  mmPerUnit: number;
  center: Vec2;
  minThicknessMm: number;
  reliefMm: number;
}

export interface ReliefView {
  setLit(ids: Set<string>): void;
}

/** A piece whose roof is height = min + relief·(F − Fmin)/(Fmax − Fmin), in mm over the tray. */
function toPiece(cell: Cell, s: ReliefScale, fMin: number, fSpan: number): PieceDef {
  const [cx, cy] = s.center;
  const k = s.reliefMm / fSpan;
  return {
    id: cell.id,
    polygon: cell.polygon.map(([x, y]) => [(x - cx) * s.mmPerUnit, (y - cy) * s.mmPerUnit]),
    roof: {
      z0: s.minThicknessMm + k * (cell.f.c + cell.f.a * cx + cell.f.b * cy - fMin),
      gx: (k * cell.f.a) / s.mmPerUnit,
      gy: (k * cell.f.b) / s.mmPerUnit,
    },
  };
}

export function createRelief(container: HTMLElement, cells: Cell[], scale: ReliefScale, onPick: (id: string) => void): ReliefView | null {
  let renderer: THREE.WebGLRenderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true });
  } catch {
    container.innerHTML = '<p class="fig-note">The 3D view needs WebGL, which is not available in this browser.</p>';
    return null;
  }
  const dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const colors = palette(dark);
  const [fMin, fMax] = range(cells);
  const pieces = cells.map((c) => toPiece(c, scale, fMin, fMax - fMin || 1));

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(colors.background);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x5d574d, 1.1));
  const sun = new THREE.DirectionalLight(0xffffff, 2.4);
  sun.position.set(-120, -60, 160);
  scene.add(sun);

  const meshes = pieces.map((piece) => {
    const geometry = pieceGeometry(piece);
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: colors.piece, flatShading: true, roughness: 0.85 }));
    mesh.userData.id = piece.id;
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry, 1), new THREE.LineBasicMaterial({ color: colors.edge }));
    scene.add(mesh, edges);
    return mesh;
  });

  const half = Math.max(...pieces.flatMap((p) => p.polygon.map(([x, y]) => Math.max(Math.abs(x), Math.abs(y)))));
  const top = scale.minThicknessMm + scale.reliefMm;
  const camera = new THREE.PerspectiveCamera(32, 4 / 3, 1, 5000);
  camera.up.set(0, 0, 1);
  camera.position.set(half * 2.0, -half * 3.7, half * 3.1);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 0, top * 0.25);
  // Turning only: zooming with the wheel would capture the page's scrolling.
  controls.enableZoom = false;
  controls.enablePan = false;
  controls.maxPolarAngle = Math.PI / 2 - 0.05;
  controls.update();

  const render = () => renderer.render(scene, camera);
  controls.addEventListener('change', render);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.append(renderer.domElement);
  new ResizeObserver(() => {
    const w = container.clientWidth;
    const h = Math.round(w * 0.75);
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    render();
  }).observe(container);

  // A click (not a drag) on a block selects its cell.
  const raycaster = new THREE.Raycaster();
  let down: { x: number; y: number } | null = null;
  renderer.domElement.addEventListener('pointerdown', (e) => { down = { x: e.clientX, y: e.clientY }; });
  renderer.domElement.addEventListener('pointerup', (e) => {
    if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 4) return;
    const rect = renderer.domElement.getBoundingClientRect();
    raycaster.setFromCamera(new THREE.Vector2(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1), camera);
    const hit = raycaster.intersectObjects(meshes)[0];
    if (hit) onPick(hit.object.userData.id as string);
  });

  return {
    setLit(ids) {
      meshes.forEach((m) => m.material.color.setHex(ids.has(m.userData.id) ? colors.selected : colors.piece));
      render();
    },
  };
}
