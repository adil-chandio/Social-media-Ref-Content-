import fs from 'node:fs/promises';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.self = dom.window;

const THREE = await import('three');
const { SVGRenderer } = await import('three/addons/renderers/SVGRenderer.js');
const { FontLoader } = await import('three/addons/loaders/FontLoader.js');
const { TextGeometry } = await import('three/addons/geometries/TextGeometry.js');
const { RoundedBoxGeometry } = await import('three/addons/geometries/RoundedBoxGeometry.js');
const { Resvg } = await import('@resvg/resvg-js');

const W = 432;
const H = 768;
const OUT_W = 720;
const OUT_H = 1280;
const FPS = 30;
const FRAMES = 698;
const DURATION = FRAMES / FPS;
const THREE_ENTRY_URL = import.meta.resolve('three');
const FONT_PATH = fileURLToPath(new URL('../examples/fonts/helvetiker_bold.typeface.json', THREE_ENTRY_URL));
const fontData = JSON.parse(await fs.readFile(FONT_PATH, 'utf8'));
const font = new FontLoader().parse(fontData);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, W / H, 0.1, 100);
camera.position.set(0, 0, 11.8);
camera.lookAt(0, 0, 0);
scene.add(new THREE.AmbientLight(0xffffff, 0.72));
const keyLight = new THREE.DirectionalLight(0xf2f5f4, 1.0);
keyLight.position.set(-3.8, 5.6, 7.5);
scene.add(keyLight);
const cyanLight = new THREE.DirectionalLight(0x39dce7, 0.5);
cyanLight.position.set(5.5, 0.2, 5.2);
scene.add(cyanLight);
const amberLight = new THREE.DirectionalLight(0xffbd55, 0.36);
amberLight.position.set(-4.2, -3.4, 3.6);
scene.add(amberLight);

const renderer = new SVGRenderer();
renderer.setSize(W, H);
renderer.setPrecision(2);
renderer.setQuality('high');

const COLORS = {
  ice: 0xd8e7e8,
  cyan: 0x21d2df,
  teal: 0x0b9f9e,
  amber: 0xf2ad43,
  gold: 0xd78e32,
  coral: 0xf24859,
  graphite: 0x171e25,
  black: 0x080c11,
  skin: 0xa57557,
  leather: 0x17191b,
  silver: 0x879398,
};

function phong(color, extra = {}) {
  return new THREE.MeshPhongMaterial({ color, specular: 0x6b8588, shininess: 52, ...extra });
}
function basic(color, extra = {}) {
  return new THREE.MeshBasicMaterial({ color, ...extra });
}
function mesh(geometry, material, parent, position = [0, 0, 0], scale = [1, 1, 1]) {
  const o = new THREE.Mesh(geometry, material);
  o.position.set(...position);
  o.scale.set(...scale);
  parent.add(o);
  return o;
}
function addText(parent, text, size, depth, material, position = [0, 0, 0], opts = {}) {
  const geometry = new TextGeometry(text, {
    font,
    size,
    depth,
    curveSegments: opts.curveSegments ?? 7,
    bevelEnabled: opts.bevel ?? true,
    bevelThickness: opts.bevelThickness ?? Math.max(0.012, size * 0.025),
    bevelSize: opts.bevelSize ?? Math.max(0.008, size * 0.018),
    bevelSegments: opts.bevelSegments ?? 2,
  });
  geometry.computeBoundingBox();
  geometry.center();
  const o = new THREE.Mesh(geometry, material);
  o.position.set(...position);
  parent.add(o);
  return o;
}
function addLine(parent, pts, color = COLORS.cyan, opacity = 1, width = 1) {
  const g = new THREE.BufferGeometry().setFromPoints(pts.map(p => new THREE.Vector3(...p)));
  const m = new THREE.LineBasicMaterial({ color, transparent: opacity < 1, opacity, linewidth: width });
  const o = new THREE.Line(g, m);
  parent.add(o);
  return o;
}
function roundedBox(parent, dims, position, material, radius = 0.08, segments = 4) {
  return mesh(new RoundedBoxGeometry(...dims, segments, radius), material, parent, position);
}
function ring(parent, radius, tube, color, position = [0, 0, 0], rotation = [0, 0, 0], opacity = 1) {
  const material = new THREE.MeshPhongMaterial({ color, emissive: color, emissiveIntensity: 0.16, specular: 0x88ffff, shininess: 90, transparent: opacity < 1, opacity });
  const o = mesh(new THREE.TorusGeometry(radius, tube, 5, 32), material, parent, position);
  o.rotation.set(...rotation);
  return o;
}
function setVisible(g, value) { g.visible = value; }
function easeOutCubic(x) { x = Math.max(0, Math.min(1, x)); return 1 - Math.pow(1 - x, 3); }
function easeOutBack(x) { x = Math.max(0, Math.min(1, x)); const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); }
function clamp01(x) { return Math.max(0, Math.min(1, x)); }
function lerp(a, b, t) { return a + (b - a) * t; }

// Floating dimensional environment: points and rings are genuine Three.js geometry.
const ambience = new THREE.Group();
scene.add(ambience);
let seed = 9052008;
function rand() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }
for (let i = 0; i < 26; i++) {
  const r = 0.018 + rand() * 0.035;
  const c = i % 5 === 0 ? COLORS.amber : (i % 3 === 0 ? COLORS.cyan : 0x66818a);
  const p = mesh(new THREE.IcosahedronGeometry(r, 0), basic(c, { transparent: true, opacity: 0.35 + rand() * 0.45 }), ambience,
    [(rand() - 0.5) * 6.4, (rand() - 0.5) * 10.2, -3.2 - rand() * 4.0]);
  p.userData.phase = rand() * Math.PI * 2;
  p.userData.baseY = p.position.y;
}
const ambientRings = new THREE.Group();
ambience.add(ambientRings);
ring(ambientRings, 2.85, 0.012, 0x1b6770, [0, 0, -2.6], [0.16, 0.12, 0.03], 0.58);
ring(ambientRings, 3.45, 0.009, 0x81572b, [0, 0, -3.0], [-0.18, 0.08, -0.05], 0.46);

// Scene 1 — a 3D money-bag reveal under the exact story beat “TWENTY BILLION”.
const opening = new THREE.Group(); scene.add(opening);
const openTitle1 = addText(opening, 'TWENTY', 0.72, 0.16, phong(COLORS.ice), [0, 2.56, 0.2], { bevelThickness: 0.022, bevelSize: 0.016 });
const openTitle2 = addText(opening, 'BILLION', 0.88, 0.22, phong(COLORS.amber), [0, 1.63, 0.28], { bevelThickness: 0.03, bevelSize: 0.023 });
const moneyBag = new THREE.Group(); opening.add(moneyBag); moneyBag.position.set(0, -1.22, 0.52);
mesh(new THREE.SphereGeometry(0.76, 28, 20), phong(0x98752f), moneyBag, [0, -0.22, 0], [0.82, 1.02, 0.58]);
mesh(new THREE.CylinderGeometry(0.23, 0.34, 0.48, 18), phong(0xb18b45), moneyBag, [0, 0.62, 0], [1, 1, 0.82]).rotation.z = -0.04;
mesh(new THREE.SphereGeometry(0.17, 18, 12), phong(0xd3ab5d), moneyBag, [0.03, 0.9, 0], [0.92, 0.8, 0.84]);
const bagTie = ring(moneyBag, 0.28, 0.052, COLORS.amber, [0, 0.52, 0], [0, 0, 0], 1);
const dollar = addText(moneyBag, '$', 0.72, 0.045, phong(0x202b27), [0, -0.25, 0.46], { bevel: false });
// Folded banknotes, each a separate 3D prop with a raised border.
for (let i = 0; i < 4; i++) {
  const note = new THREE.Group(); moneyBag.add(note);
  const angle = (i / 4) * Math.PI * 2 + 0.4;
  note.position.set(Math.cos(angle) * 1.02, -0.12 + (i % 2) * 0.24, 0.05 - i * 0.07);
  note.rotation.set(0.08 * (i % 2), 0.12 * i, Math.sin(angle) * 0.33);
  roundedBox(note, [0.76, 0.4, 0.055], [0, 0, 0], phong(i % 2 ? 0x1d7f6d : 0x274b43), 0.035, 3);
  roundedBox(note, [0.61, 0.28, 0.02], [0, 0, 0.04], phong(0x8ebc8a), 0.018, 3);
  ring(note, 0.095, 0.012, COLORS.amber, [0, 0, 0.065], [0, 0, 0], 0.95);
}
const bagStage = new THREE.Group(); opening.add(bagStage);
roundedBox(bagStage, [1.76, 0.15, 0.64], [0, -2.42, 0.12], phong(0x73572f), 0.07, 2);
for (const x of [-0.62, 0.62]) for (const z of [-0.16, 0.28]) {
  mesh(new THREE.CylinderGeometry(0.045, 0.055, 0.88, 10), phong(0x51432f), bagStage, [x, -2.9, z]);
}
roundedBox(bagStage, [1.22, 0.08, 0.42], [0, -2.82, 0.09], phong(0x58472f), 0.035, 2);
ring(opening, 1.53, 0.026, COLORS.cyan, [0, -1.2, -0.05], [0.0, 0.22, 0.0], 0.9);
ring(opening, 1.68, 0.012, COLORS.amber, [0, -1.2, -0.12], [0.0, -0.18, 0.05], 0.68);

// 3D GPU prop builder shared by the year, future and end-card shots.
function createGpu(scale = 1) {
  const root = new THREE.Group();
  const shellMat = phong(0x172126);
  const boardMat = phong(0x173e3c);
  const goldMat = phong(0xc29043);
  // Broad, beveled board silhouette with a compact geometry budget for reliable animation renders.
  roundedBox(root, [3.34, 1.78, 0.3], [0, 0, 0], shellMat, 0.12, 2);
  roundedBox(root, [3.08, 1.54, 0.08], [0, 0, 0.18], boardMat, 0.09, 2);
  roundedBox(root, [1.12, 0.76, 0.22], [0, 0, 0.34], phong(0x222c31), 0.07, 2);
  roundedBox(root, [0.91, 0.48, 0.055], [0, 0, 0.48], phong(0x101a20), 0.03, 2);
  addText(root, 'AI', 0.31, 0.045, phong(COLORS.cyan), [0, 0.02, 0.515], { bevel: false, curveSegments: 4 });
  // Two readable fan wells, built from low-poly circles, rings and radial metal struts.
  for (const x of [-1.08, 1.08]) {
    const fan = new THREE.Group(); root.add(fan); fan.position.set(x, 0, 0.31);
    mesh(new THREE.CircleGeometry(0.54, 18), basic(0x0a1116), fan, [0, 0, 0.025]);
    ring(fan, 0.51, 0.028, x < 0 ? COLORS.cyan : COLORS.amber, [0, 0, 0.06], [0, 0, 0], 1);
    ring(fan, 0.35, 0.014, 0x72858b, [0, 0, 0.075], [0, 0, 0], 0.88);
    for (let j = 0; j < 4; j++) {
      const a = j * Math.PI / 2 + 0.2;
      addLine(fan, [[Math.cos(a)*0.14,Math.sin(a)*0.14,0.10],[Math.cos(a+0.55)*0.43,Math.sin(a+0.55)*0.43,0.10]], 0x71848a, 0.9);
    }
    mesh(new THREE.CircleGeometry(0.13, 12), phong(0x9eaeb0), fan, [0, 0, 0.12]);
  }
  const traces = [
    [[-0.55,0.49,0.24],[-0.84,0.49,0.24],[-1.0,0.65,0.24],[-1.42,0.65,0.24]],
    [[0.55,0.49,0.24],[0.84,0.49,0.24],[1.0,0.65,0.24],[1.42,0.65,0.24]],
    [[-0.55,-0.48,0.24],[-0.84,-0.48,0.24],[-1.0,-0.63,0.24],[-1.42,-0.63,0.24]],
    [[0.55,-0.48,0.24],[0.84,-0.48,0.24],[1.0,-0.63,0.24],[1.42,-0.63,0.24]],
  ];
  traces.forEach((pts, i) => addLine(root, pts, i % 2 ? COLORS.amber : COLORS.cyan, 0.95));
  for (const x of [-1.36, -1.12, 1.12, 1.36]) roundedBox(root, [0.10, 0.16, 0.06], [x, -0.99, 0.12], goldMat, 0.015, 1);
  root.scale.setScalar(scale);
  return root;
}

// Scene 2 — NO lands as a sculpted 3D title, with a cloud of metal/graphite forms.
const noScene = new THREE.Group(); scene.add(noScene);
const cloud = new THREE.Group(); noScene.add(cloud);
for (let i = 0; i < 11; i++) {
  const r = 0.24 + (i % 3) * 0.1;
  mesh(new THREE.SphereGeometry(r, 16, 10), phong(i % 2 ? 0x657179 : 0x49535a, { transparent: true, opacity: 0.55 }), cloud,
    [-2.15 + i * 0.43, 2.45 + Math.sin(i * 1.7) * 0.16, -0.8 + (i % 4) * 0.04], [1.1, 0.68, 0.52]);
}
const heSaid = addText(noScene, 'HE SAID', 0.58, 0.15, phong(COLORS.ice), [0, 1.35, 0.2]);
const noWord = addText(noScene, 'NO', 2.22, 0.4, phong(COLORS.coral, { specular: 0xff8891, shininess: 110 }), [0, -0.24, 0.32], { bevelThickness: 0.07, bevelSize: 0.06, bevelSegments: 3 });
const noShadow = addText(noScene, 'NO', 2.22, 0.34, phong(0x631923), [0.08, -0.34, -0.16], { bevelThickness: 0.05, bevelSize: 0.045, bevelSegments: 2 });
const stamp = new THREE.Group(); noScene.add(stamp);
roundedBox(stamp, [2.65, 0.36, 0.62], [0, -1.83, 0.0], phong(0x252d34), 0.12, 5);
roundedBox(stamp, [2.32, 0.1, 0.16], [0, -1.62, 0.02], phong(COLORS.coral), 0.045, 3);
const shock = ring(noScene, 1.22, 0.035, COLORS.coral, [0, -0.85, -0.55], [0, 0, 0], 0.8);
const shock2 = ring(noScene, 1.72, 0.018, COLORS.cyan, [0, -0.85, -0.72], [0.08, 0.1, 0], 0.48);
for (let i = 0; i < 9; i++) {
  const shard = mesh(new THREE.TetrahedronGeometry(0.16 + (i%3)*0.07), phong(i%2?COLORS.coral:COLORS.amber), noScene,
    [(rand()-0.5)*4.2, -0.5 + rand()*2.8, -0.2 + rand()*0.4]);
  shard.userData.seed = rand() * 10;
  shard.userData.baseY = shard.position.y;
}

// Scene 3 — the 2008 turning point and the first GPU core.
const yearScene = new THREE.Group(); scene.add(yearScene);
const yearBack = addText(yearScene, '2008', 1.28, 0.23, phong(COLORS.ice), [0, 1.52, -0.1], { bevelThickness: 0.032, bevelSize: 0.024 });
const yearGlow = addText(yearScene, '2008', 1.28, 0.15, basic(COLORS.cyan, { transparent: true, opacity: 0.16 }), [0.04, 1.49, -0.46], { bevel: false });
const nvidiaYear = addText(yearScene, 'NVIDIA', 0.39, 0.1, phong(COLORS.cyan), [0, 0.28, 0.25], { bevel: false, curveSegments: 4 });
const yearChip = createGpu(0.72); yearScene.add(yearChip); yearChip.position.set(0, -1.22, 0.25);
addText(yearScene, 'A TURNING POINT', 0.37, 0.08, phong(COLORS.amber), [0, -2.78, 0.25], { bevel: false, curveSegments: 5 });
const yearOrbit = new THREE.Group(); yearScene.add(yearOrbit);
ring(yearOrbit, 2.12, 0.022, COLORS.cyan, [0, -0.12, -0.3], [0.25, 0.12, 0.0], 0.86);
ring(yearOrbit, 2.4, 0.012, COLORS.amber, [0, -0.12, -0.42], [-0.2, 0.14, 0.03], 0.66);
for (let i = 0; i < 12; i++) {
  const a = i * Math.PI * 2 / 12;
  const p1=[Math.cos(a)*2.0, Math.sin(a)*2.0-0.1,-0.25];
  const p2=[Math.cos(a)*2.3, Math.sin(a)*2.3-0.1,-0.25];
  addLine(yearScene,[p1,p2],i%3===0?COLORS.amber:COLORS.cyan,0.75);
}

// Scene 4 — an original, stylized 3D founder bust; no flattened source portrait is reused.
const founderScene = new THREE.Group(); scene.add(founderScene);
const founderBackdrop = addText(founderScene, '2008', 1.28, 0.18, basic(COLORS.cyan, { transparent: true, opacity: 0.17 }), [0, 2.62, -1.1], { bevel: false });
const founder = new THREE.Group(); founderScene.add(founder); founder.position.set(0, -0.36, 0.36);
const jacketMat = phong(COLORS.leather, { specular: 0x526168, shininess: 75 });
const jacket = roundedBox(founder, [1.82, 1.76, 0.72], [0, -1.16, 0], jacketMat, 0.42, 7);
// A subtle center seam and lapel-like metallic folds.
addLine(founder, [[0,-0.35,0.38],[0,-1.95,0.38]], 0x697276, 0.7);
const lapelL = new THREE.Shape(); lapelL.moveTo(-0.66,-0.42); lapelL.lineTo(-0.12,-0.22); lapelL.lineTo(-0.28,-1.12); lapelL.lineTo(-0.76,-0.7); lapelL.closePath();
const lapelR = new THREE.Shape(); lapelR.moveTo(0.66,-0.42); lapelR.lineTo(0.12,-0.22); lapelR.lineTo(0.28,-1.12); lapelR.lineTo(0.76,-0.7); lapelR.closePath();
for (const sh of [lapelL,lapelR]) {
  const lapelGeo = new THREE.ExtrudeGeometry(sh,{depth:0.045,bevelEnabled:true,bevelThickness:0.015,bevelSize:0.012,bevelSegments:1});
  mesh(lapelGeo,phong(0x2c3439),founder,[0,0,0.395]);
}
mesh(new THREE.CylinderGeometry(0.26,0.31,0.5,18), phong(COLORS.skin), founder, [0, -0.25, 0.08]);
const head = new THREE.Group(); founder.add(head); head.position.set(0, 0.54, 0.14);
mesh(new THREE.SphereGeometry(0.62,24,18),phong(COLORS.skin),head,[0,0,0],[0.82,1.03,0.75]);
// ears
for (const x of [-0.5,0.5]) mesh(new THREE.SphereGeometry(0.14,14,10),phong(COLORS.skin),head,[x,-0.04,0],[0.72,1,0.65]);
// brushed silver hair cap and side locks
mesh(new THREE.SphereGeometry(0.53,20,14),phong(0x5d696b),head,[0,0.42,-0.06],[0.86,0.34,0.72]);
for (const x of [-0.38,0.38]) mesh(new THREE.SphereGeometry(0.18,14,10),phong(0x4d595b),head,[x,0.2,-0.12],[0.72,1.15,0.72]);
// brow, nose, mouth; face is intentionally stylized rather than photorealistic.
for (const x of [-0.17,0.17]) {
  mesh(new THREE.SphereGeometry(0.047,10,7),phong(0x1b2022),head,[x,0.04,0.45],[1,0.7,0.7]);
  mesh(new THREE.CircleGeometry(0.12,16),new THREE.MeshPhongMaterial({color:0x5b838a,transparent:true,opacity:0.13,side:THREE.DoubleSide}),head,[x,0.03,0.485]);
  mesh(new THREE.TorusGeometry(0.14,0.018,5,20),phong(0x9bb3b2),head,[x,0.03,0.49]);
}
addLine(head,[[-0.015,0.03,0.5],[0.0,-0.13,0.54],[0.07,-0.17,0.51]],0x74503d,0.8);
addLine(head,[[-0.12,-0.31,0.48],[0,-0.34,0.51],[0.12,-0.31,0.48]],0x553933,0.95);
addLine(head,[[-0.015,0.03,0.47],[0.015,0.03,0.47]],0x879294,0.95);
// hands and sleeves provide a natural bust silhouette.
for (const side of [-1,1]) {
  const arm = mesh(new THREE.CapsuleGeometry(0.25,0.78,4,10),jacketMat,founder,[side*0.78,-1.18,0.02]);
  arm.rotation.z = side * -0.13;
  mesh(new THREE.SphereGeometry(0.18,12,9),phong(COLORS.skin),founder,[side*0.72,-0.62,0.13],[0.86,1.05,0.72]);
}
const founderPedestal = new THREE.Group(); founderScene.add(founderPedestal);
mesh(new THREE.CylinderGeometry(1.15,1.26,0.16,40),phong(0x1b282e),founderPedestal,[0,-3.04,0]).rotation.x=Math.PI/2;
ring(founderScene,1.7,0.022,COLORS.amber,[0,-2.95,-0.1],[0.14,0.0,0.0],0.7);
const founderCaption = addText(founderScene,'ONE VISION',0.52,0.12,phong(COLORS.ice),[0,-3.4,0.3],{bevel:false});

// Scene 5 — GPU at the center of an AI / gaming constellation.
const futureScene = new THREE.Group(); scene.add(futureScene);
const futureGpu = createGpu(0.98); futureScene.add(futureGpu); futureGpu.position.set(0, 0.1, 0.25);
const futureHalo = new THREE.Group(); futureScene.add(futureHalo);
const halo1 = ring(futureHalo,2.12,0.026,COLORS.cyan,[0,0,0.0],[0.2,0.05,0.0],0.98);
const halo2 = ring(futureHalo,2.52,0.017,COLORS.amber,[0,0,-0.18],[-0.22,0.08,0.02],0.76);
const aiLabel = addText(futureScene,'AI',0.8,0.18,phong(COLORS.ice),[-1.48,2.35,0.25]);
const gameLabel = addText(futureScene,'GAMING',0.49,0.13,phong(COLORS.amber),[0,-2.25,0.25],{bevelThickness:0.015,bevelSize:0.012});
const visionLabel = addText(futureScene,'POWERING TOMORROW',0.31,0.08,phong(COLORS.cyan),[0,-3.0,0.25],{bevel:false,curveSegments:5});
for (let i=0;i<8;i++) {
  const a=i*Math.PI/4;
  const x=Math.cos(a)*2.25, y=Math.sin(a)*2.25;
  const node=mesh(new THREE.IcosahedronGeometry(0.075,1),phong(i%2?COLORS.cyan:COLORS.amber),futureScene,[x,y,-0.04]);
  addLine(futureScene,[[Math.cos(a)*1.73,Math.sin(a)*1.73,-0.02],[x,y,-0.02]],i%2?COLORS.cyan:COLORS.amber,0.78);
}

// Scene 6 — 3D end card and subscribe control.
const ctaScene = new THREE.Group(); scene.add(ctaScene);
const ctaChip = createGpu(0.78); ctaScene.add(ctaChip); ctaChip.position.set(0,1.48,-0.18);
const ctaHeadline = addText(ctaScene,'THE FUTURE',0.52,0.13,phong(COLORS.ice),[0,3.05,0.25],{curveSegments:4,bevelSegments:1,bevelThickness:0.014,bevelSize:0.01});
const ctaSub = addText(ctaScene,'IS BUILT ON VISION',0.28,0.07,phong(COLORS.amber),[0,2.48,0.25],{bevel:false,curveSegments:4});
const button = new THREE.Group(); ctaScene.add(button); button.position.set(0,-1.24,0.52);
roundedBox(button,[3.24,0.82,0.5],[0,0,0],phong(0x122329),0.22,7);
roundedBox(button,[2.94,0.58,0.11],[0,0,0.29],phong(0x24424a),0.15,6);
const buttonText = addText(button,'SUBSCRIBE',0.49,0.10,phong(COLORS.ice),[0,0.01,0.39],{bevel:false,curveSegments:4});
ring(button,1.92,0.025,COLORS.cyan,[0,0,-0.4],[0,0,0],0.78);
const ctaPedestal = new THREE.Group(); ctaScene.add(ctaPedestal);
mesh(new THREE.CylinderGeometry(2.05,2.25,0.2,48),phong(0x202931),ctaPedestal,[0,-3.42,-0.05]).rotation.x=Math.PI/2;
ring(ctaScene,2.0,0.024,COLORS.amber,[0,-3.3,-0.02],[0.12,0,0],0.8);

const phases = [
  { name:'opening', start:0.0, end:3.25, top:'A BILLION-DOLLAR DECISION', bottom:'THE AMBITION' },
  { name:'no', start:3.25, end:5.9, top:'THE ANSWER WAS NO', bottom:'THE REJECTION' },
  { name:'year', start:5.9, end:8.8, top:'A DEFINING MOMENT', bottom:'THE TURNING POINT' },
  { name:'founder', start:8.8, end:13.65, top:'VISION OVER DOUBT', bottom:'VISION OVER DOUBT' },
  { name:'future', start:13.65, end:19.5, top:'THE CHIP THAT CHANGED EVERYTHING', bottom:'AI • GAMING • FUTURE' },
  { name:'cta', start:19.5, end:DURATION, top:'THE FUTURE IS BUILT ON VISION', bottom:'STAY FOR THE NEXT STORY' },
];
const groupByName = { opening, no: noScene, year: yearScene, founder: founderScene, future: futureScene, cta: ctaScene };

function phaseAt(t) { return phases.find(p => t >= p.start && t < p.end) ?? phases.at(-1); }
function updateFrame(t) {
  const phase = phaseAt(t);
  for (const p of phases) setVisible(groupByName[p.name], p.name === phase.name);
  const local = t - phase.start;
  const progress = clamp01(local / (phase.end - phase.start));
  ambience.rotation.y = t * 0.018;
  ambience.rotation.x = Math.sin(t * 0.22) * 0.012;
  for (const p of ambience.children) {
    if (p.userData.phase !== undefined) p.position.y = p.userData.baseY + Math.sin(t * 0.75 + p.userData.phase) * 0.035;
  }
  camera.position.x = Math.sin(t * 0.31) * 0.09;
  camera.position.y = Math.cos(t * 0.23) * 0.055;
  camera.position.z = 11.8;
  camera.lookAt(0, 0, 0);

  if (phase.name === 'opening') {
    const enter = easeOutBack(progress / 0.36);
    const titleIn1 = easeOutBack(progress / 0.18);
    const titleIn2 = easeOutBack((progress - 0.13) / 0.22);
    const bagIn = easeOutBack((progress - 0.06) / 0.19);
    opening.scale.setScalar(0.9 + 0.1 * enter);
    opening.position.y = Math.sin(t * 1.4) * 0.035;
    openTitle1.scale.setScalar(0.52 + 0.48 * titleIn1);
    openTitle1.position.y = 2.56 + 0.27 * (1-titleIn1) + Math.sin(t * 2.3) * 0.04;
    openTitle2.scale.setScalar(0.52 + 0.48 * titleIn2);
    openTitle2.position.y = 1.58 + 0.28 * (1-titleIn2) + Math.sin(t * 2.0 + 1) * 0.035;
    moneyBag.scale.setScalar(0.72 + 0.28 * bagIn);
    moneyBag.rotation.y = Math.sin(t * 1.3) * 0.13;
    moneyBag.rotation.z = Math.sin(t * 2.1) * 0.035;
    moneyBag.position.y = -1.19 - 2.7 * (1-bagIn) + Math.sin(t * 2.0) * 0.05;
    bagStage.rotation.z = Math.sin(t) * 0.025;
    camera.position.z = 12.55 - 0.75 * easeOutCubic(progress / 0.32);
    camera.lookAt(0,0,0);
  }
  if (phase.name === 'no') {
    const hit = easeOutBack(progress / 0.32);
    const s = Math.max(0.02, hit);
    noWord.scale.setScalar(s);
    noShadow.scale.setScalar(s);
    noWord.rotation.z = Math.sin(local * 7) * 0.012 * (1-progress);
    cloud.position.x = Math.sin(local * 1.2) * 0.11;
    stamp.rotation.z = -0.045 + Math.sin(local * 4) * 0.012;
    shock.scale.setScalar(0.65 + progress * 1.4);
    shock.material.opacity = 0.75 * (1-progress*0.52);
    shock2.scale.setScalar(0.8 + progress * 1.1);
    shock2.material.opacity = 0.45 * (1-progress*0.55);
    for (const o of noScene.children) if (o.userData.seed !== undefined) {
      o.rotation.x = local * 0.7 + o.userData.seed;
      o.rotation.y = local * 0.9 + o.userData.seed * 0.5;
      o.position.y = o.userData.baseY + Math.sin(local*2 + o.userData.seed) * 0.05;
    }
  }
  if (phase.name === 'year') {
    const enter = easeOutCubic(progress / 0.35);
    yearScene.scale.setScalar(0.88 + 0.12 * enter);
    yearBack.position.y = 1.5 + Math.sin(local * 1.9) * 0.06;
    yearBack.rotation.y = Math.sin(local*0.6)*0.08;
    yearChip.rotation.y = Math.sin(local*0.9)*0.2;
    yearChip.rotation.x = -0.08 + Math.sin(local*0.7)*0.04;
    yearChip.position.y = -1.22 + Math.sin(local*2.3)*0.07;
    yearOrbit.rotation.z = local * 0.27;
  }
  if (phase.name === 'founder') {
    const enter = easeOutCubic(progress / 0.24);
    founderScene.scale.setScalar(0.94 + 0.06*enter);
    founder.rotation.y = Math.sin(local*0.82)*0.07;
    head.rotation.x = Math.sin(local*1.1)*0.018;
    head.rotation.z = Math.sin(local*0.9)*0.018;
    founderBackdrop.scale.setScalar(1 + Math.sin(local*1.7)*0.025);
    founderPedestal.rotation.y = local*0.14;
  }
  if (phase.name === 'future') {
    const enter = easeOutCubic(progress / 0.22);
    futureScene.scale.setScalar(0.86 + 0.14*enter);
    futureGpu.rotation.y = Math.sin(local*0.7)*0.22;
    futureGpu.rotation.x = Math.sin(local*0.55)*0.08;
    futureGpu.rotation.z = Math.sin(local*0.4)*0.04;
    futureGpu.position.y = 0.12 + Math.sin(local*1.6)*0.07;
    futureHalo.rotation.z = local*0.35;
    futureHalo.rotation.y = Math.sin(local*0.25)*0.16;
  }
  if (phase.name === 'cta') {
    const enter = easeOutBack(progress/0.22);
    const buttonIn = easeOutBack(progress/0.18);
    ctaScene.scale.setScalar(0.94 + 0.06*enter);
    ctaChip.rotation.y = local*0.35;
    ctaChip.rotation.x = -0.08 + Math.sin(local)*0.04;
    ctaChip.position.y = 1.52 + 0.55*(1-easeOutCubic(progress/0.24)) + Math.sin(local*1.25)*0.045;
    button.position.y = -1.24 - 0.48*(1-easeOutCubic(progress/0.2));
    const pulse = 0.018*Math.sin(local*3.2);
    button.scale.setScalar(0.8 + 0.2*buttonIn + pulse);
    button.rotation.z = Math.sin(local*1.2)*0.012;
  }
  return phase;
}

const BACKDROPS = {
  opening: ['#070b11','#101c22','#1c2020','#080b0e','#f1ad48'],
  no: ['#100b11','#28131a','#311116','#080a10','#f24859'],
  year: ['#071219','#0b2228','#15353a','#060b11','#21d2df'],
  founder: ['#071116','#0c1f22','#122b2e','#060a0f','#f2ad43'],
  future: ['#060d14','#0b2027','#0e3438','#05090e','#21d2df'],
  cta: ['#070c12','#111923','#19242a','#070b10','#f2ad43'],
};
function decorateSvg(rawSvg, t, phase) {
  const pal = BACKDROPS[phase.name];
  const rootMatch = rawSvg.match(/^<svg[^>]*>/);
  const originalRoot = rootMatch[0];
  const root = originalRoot.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ');
  const body = rawSvg.slice(originalRoot.length, rawSvg.lastIndexOf('</svg>'));
  const x = -W/2, y = -H/2;
  const glowX = Math.sin(t*0.28) * 38;
  const glowY = -65 + Math.cos(t*0.22) * 22;
  const elapsed = t / DURATION;
  const progressWidth = 366 * elapsed;
  let flash = 0;
  for (const p of phases.slice(1)) flash = Math.max(flash, Math.max(0, 1-Math.abs(t-p.start)/0.07)*0.16);
  const svg = `${root}<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${pal[0]}"/><stop offset="0.42" stop-color="${pal[1]}"/><stop offset="0.78" stop-color="${pal[2]}"/><stop offset="1" stop-color="${pal[3]}"/></linearGradient>
    <radialGradient id="aura"><stop offset="0" stop-color="${pal[4]}" stop-opacity="0.25"/><stop offset="0.43" stop-color="${pal[4]}" stop-opacity="0.10"/><stop offset="1" stop-color="${pal[4]}" stop-opacity="0"/></radialGradient>
    <radialGradient id="vignette"><stop offset="0.43" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.64"/></radialGradient>
    <linearGradient id="progress" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#21d2df"/><stop offset="1" stop-color="#f2ad43"/></linearGradient>
  </defs>
  <rect x="${x}" y="${y}" width="${W}" height="${H}" fill="url(#bg)"/>
  <ellipse cx="${glowX}" cy="${glowY}" rx="228" ry="280" fill="url(#aura)"/>
  <path d="M${x} ${-72+Math.sin(t*0.35)*8} Q0 ${-117+Math.cos(t*0.23)*13} ${-x} ${-66+Math.sin(t*0.35+0.4)*8}" fill="none" stroke="${pal[4]}" stroke-opacity="0.15" stroke-width="1.2"/>
  ${body}
  <rect x="${x}" y="${y}" width="${W}" height="${H}" fill="url(#vignette)"/>
  <g font-family="DejaVu Sans,Arial,sans-serif" fill="#dce7e8">
    <text x="${x+25}" y="${y+31}" font-size="8.5" letter-spacing="1.45" fill-opacity="0.77">NVIDIA  /  THE ORIGIN STORY</text>
    <text x="${-x-25}" y="${y+31}" text-anchor="end" font-size="8.5" letter-spacing="1.2" fill-opacity="0.55">${String(Math.floor(t / 60)).padStart(2,'0')} : ${String(Math.floor(t % 60)).padStart(2,'0')}</text>
    <text x="0" y="${-y-43}" text-anchor="middle" font-size="8.8" letter-spacing="1.7" fill-opacity="0.72">${phase.bottom}</text>
  </g>
  <rect x="${x+25}" y="${-y-23}" width="366" height="2.4" rx="1.2" fill="#dce7e8" fill-opacity="0.16"/>
  <rect x="${x+25}" y="${-y-23}" width="${Math.max(0.5,progressWidth)}" height="2.4" rx="1.2" fill="url(#progress)"/>
  ${flash>0?`<rect x="${x}" y="${y}" width="${W}" height="${H}" fill="#eaffff" fill-opacity="${flash.toFixed(3)}"/>`:''}
  </svg>`;
  return svg;
}

async function renderPng(t) {
  const start = performance.now();
  const phase = updateFrame(t);
  renderer.render(scene, camera);
  const rendered = performance.now();
  const svg = decorateSvg(renderer.domElement.outerHTML, t, phase);
  // Resvg's XML parser needs a concrete namespace and clamps any renderer overbright RGB values.
  const png = new Resvg(svg, { fitTo: { mode: 'width', value: OUT_W }, font: { loadSystemFonts: true }, logLevel: 'off' }).render().asPng();
  if (process.env.TIMING) console.log(`timing ${phase.name} t=${t.toFixed(2)} render=${((rendered-start)/1000).toFixed(3)}s raster=${((performance.now()-rendered)/1000).toFixed(3)}s bytes=${png.length}`);
  return png;
}

const args = process.argv.slice(2);
if (args[0] === '--preview') {
  const times = args.slice(1).map(Number);
  const outDir = path.resolve(__dirname, 'preview3d');
  await fs.mkdir(outDir, { recursive: true });
  for (const t of times) {
    const png = await renderPng(t);
    const outfile = path.join(outDir, `frame-${t.toFixed(2).replace('.', '_')}.png`);
    await fs.writeFile(outfile, png);
    console.log(`preview ${t.toFixed(2)}s -> ${outfile}`);
  }
} else if (args[0] === '--frames') {
  const worker = Number(args[1]);
  const workers = Number(args[2]);
  const outDir = path.resolve(args[3] ?? 'frames_3d');
  if (!Number.isInteger(worker) || !Number.isInteger(workers) || workers < 1 || worker < 0 || worker >= workers) throw new Error('Usage: --frames <worker-index> <worker-count> <output-dir>');
  await fs.mkdir(outDir, { recursive: true });
  const totalForWorker = Math.ceil((FRAMES - worker) / workers);
  let completed = 0;
  const began = Date.now();
  for (let i = worker; i < FRAMES; i += workers) {
    const png = await renderPng(i / FPS);
    const outfile = path.join(outDir, `frame_${String(i).padStart(4, '0')}.png`);
    await fs.writeFile(outfile, png);
    completed++;
    if (completed % 15 === 0 || completed === totalForWorker) {
      const elapsed = (Date.now() - began) / 1000;
      console.log(`worker ${worker+1}/${workers}: ${completed}/${totalForWorker} frames, elapsed ${elapsed.toFixed(0)}s`);
    }
  }
  console.log(`worker ${worker+1}/${workers} complete`);
} else if (args[0] === '--stream') {
  const ffmpeg = process.env.FFMPEG_PATH;
  if (!ffmpeg) throw new Error('Set FFMPEG_PATH to the bundled ffmpeg executable.');
  const audioBed = args[1];
  const voice = args[2];
  const output = args[3];
  if (!audioBed || !voice || !output) throw new Error('Usage: --stream <music-bed.mp4> <voice.wav> <output.mp4>');
  const graph = '[1:a]aresample=44100,volume=0.11,afade=t=out:st=22.5:d=0.7[bed];[2:a]aresample=44100,aformat=channel_layouts=stereo,volume=1.22,adelay=150:all=1,afade=t=out:st=18.2:d=0.35[vo];[bed][vo]amix=inputs=2:duration=longest:dropout_transition=0.2:normalize=0,alimiter=limit=0.96[a]';
  const child = spawn(ffmpeg, ['-y','-hide_banner','-loglevel','error','-f','image2pipe','-framerate',String(FPS),'-vcodec','png','-i','pipe:0','-i',audioBed,'-i',voice,'-filter_complex',graph,'-map','0:v:0','-map','[a]','-t','23.35','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','-r',String(FPS),'-c:a','aac','-b:a','192k','-ar','44100','-ac','2','-metadata','title=NVIDIA Origin Story | 3D Urdunglish Reel','-movflags','+faststart',output], { stdio: ['pipe','inherit','inherit'] });
  const exitPromise = new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('close', code => code === 0 ? resolve() : reject(new Error(`ffmpeg exited with code ${code}`)));
  });
  for (let i=0; i<FRAMES; i++) {
    const t = i / FPS;
    const png = await renderPng(t);
    if (!child.stdin.write(png)) await new Promise(resolve => child.stdin.once('drain', resolve));
    if (i % 30 === 0 || i === FRAMES-1) console.log(`rendered ${i+1}/${FRAMES} (${t.toFixed(2)}s)`);
  }
  child.stdin.end();
  await exitPromise;
  console.log(`wrote ${output}`);
} else {
  console.log('Usage: node procedural_reel.mjs --preview 1 4 7 ... | --stream <audioBed.mp4> <voice.wav> <output.mp4>');
}
