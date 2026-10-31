/* Adil Chandio — portfolio v3: single-rAF motion engine.
   One ticker drives cursor, parallax, tilt, glare, magnets, nav + progress.
   No scroll handlers, no competing transforms, no layout thrash → zero jerk. */
'use strict';
const CONFIG = {
  // Wire your real inbox here; until then the form points visitors to GitHub.
  email: '',
  github: 'https://github.com/adil-chandio'
};
const KEY = 'ac_intro_seen';
const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const fine = matchMedia('(pointer: fine)').matches;
const gate = $('#gate'), splash = $('#splash'), film = $('#film'), pct = $('#filmPct');
const nav = $('#nav'), prog = $('#prog'), cursor = $('#cursor'), ring = $('#cursorRing');
const toastEl = $('#toast');
let toastT;

function toast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  clearTimeout(toastT);
  toastT = setTimeout(() => toastEl.classList.remove('show'), 3200);
}

/* ── Intro film flow ─────────────────────────────────────────── */
const unlockScroll = () => document.body.classList.remove('locked');
const lockScroll = () => document.body.classList.add('locked');

function endIntro() {
  film.pause();
  splash.classList.add('done');
  unlockScroll();
  sessionStorage.setItem(KEY, '1');
}
function playSplash() {
  gate.classList.add('hidden');
  splash.classList.remove('hidden', 'done');
  lockScroll();
  film.currentTime = 0;
  const p = film.play();
  const open = () => splash.classList.add('open');
  if (p && p.then) p.then(open).catch(() => { open(); toast('Tap SKIP to enter the site'); });
  else open();
}
function boot() {
  if (sessionStorage.getItem(KEY)) {
    gate.classList.add('hidden');
    splash.classList.add('hidden', 'done');
    unlockScroll();
  } else {
    requestAnimationFrame(() => {
      gate.querySelector('.gate-name').classList.add('in');
      const k = gate.querySelector('[data-scramble]');
      if (k && !reduced) setTimeout(() => scramble(k), 350);
    });
  }
}
$('#enterBtn').addEventListener('click', playSplash);
$('#skipBtn').addEventListener('click', endIntro);
$('#replayBtn').addEventListener('click', () => {
  sessionStorage.removeItem(KEY);
  playSplash();
  window.scrollTo({ top: 0, behavior: 'auto' });
});
film.addEventListener('ended', endIntro);
film.addEventListener('timeupdate', () => {
  if (film.duration) pct.textContent = Math.round((film.currentTime / film.duration) * 100) + '%';
});
film.addEventListener('click', endIntro);

/* ── Scramble + counters + reveals ───────────────────────────── */
const GLYPHS = '█▓▒░<>/\\|=+*·01';
function scramble(el) {
  if (el.dataset.busy) return;
  el.dataset.busy = '1';
  const final = el.dataset.txt || (el.dataset.txt = el.textContent);
  let f = 0;
  const total = 16;
  const id = setInterval(() => {
    f++;
    el.textContent = final.split('').map((ch, i) =>
      (ch === ' ' || i < (f / total) * final.length) ? ch : GLYPHS[(Math.random() * GLYPHS.length) | 0]
    ).join('');
    if (f >= total) { clearInterval(id); el.textContent = final; }
  }, 34);
}
function countUp(el) {
  if (el.dataset.done) return;
  el.dataset.done = '1';
  const target = +el.dataset.count, pad = +(el.dataset.pad || 0);
  const t0 = performance.now(), dur = 1100;
  (function step(t) {
    const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
    el.textContent = String(Math.round(target * e)).padStart(pad, '0');
    if (k < 1) requestAnimationFrame(step);
  })(t0);
}
const ioRv = new IntersectionObserver((es) => es.forEach((e) => {
  if (!e.isIntersecting) return;
  e.target.classList.add('in');
  if (e.target.hasAttribute('data-scramble') && !reduced) scramble(e.target);
  ioRv.unobserve(e.target);
}), { threshold: 0.18 });
$$('[data-rv]').forEach((el) => ioRv.observe(el));
const ioCt = new IntersectionObserver((es) => es.forEach((e) => {
  if (e.isIntersecting) { countUp(e.target); ioCt.unobserve(e.target); }
}), { threshold: 0.5 });
$$('[data-count]').forEach((el) => ioCt.observe(el));

/* ── Motion engine: one ticker, lerped writes, batched reads ─── */
let mx = innerWidth / 2, my = innerHeight / 2, cx = mx, cy = my, curOn = false;
const P = $$('[data-px]').map((el) => ({ el, sp: parseFloat(el.dataset.px) || 0, base: el.dataset.base || '', y: 0, ty: 0 }));
const T = $$('[data-tilt]').map((el) => ({ el, st: parseFloat(el.dataset.tilt) || 7, rx: 0, ry: 0, trx: 0, try_: 0 }));
const M = $$('.magnet').map((el) => ({ el, dx: 0, dy: 0, tx: 0, ty: 0 }));

addEventListener('mousemove', (e) => {
  mx = e.clientX; my = e.clientY;
  if (!curOn && fine && !reduced) { curOn = true; document.body.classList.add('cur'); }
}, { passive: true });

M.forEach((m) => {
  m.el.addEventListener('mousemove', (e) => {
    const r = m.el.getBoundingClientRect();
    m.tx = (e.clientX - r.left - r.width / 2) * 0.26;
    m.ty = (e.clientY - r.top - r.height / 2) * 0.32;
  }, { passive: true });
  m.el.addEventListener('mouseleave', () => { m.tx = 0; m.ty = 0; }, { passive: true });
});
T.forEach((t) => {
  t.el.addEventListener('mousemove', (e) => {
    const r = t.el.getBoundingClientRect();
    const nx = (e.clientX - r.left) / r.width - 0.5;
    const ny = (e.clientY - r.top) / r.height - 0.5;
    t.trx = -ny * t.st; t.try_ = nx * t.st;
    t.el.style.setProperty('--gx', ((nx + 0.5) * 100).toFixed(1) + '%');
    t.el.style.setProperty('--gy', ((ny + 0.5) * 100).toFixed(1) + '%');
  }, { passive: true });
  t.el.addEventListener('mouseleave', () => { t.trx = 0; t.try_ = 0; }, { passive: true });
});
$$('a,button,.work-card,.sk').forEach((el) => {
  el.addEventListener('mouseenter', () => document.body.classList.add('cur-hot'), { passive: true });
  el.addEventListener('mouseleave', () => document.body.classList.remove('cur-hot'), { passive: true });
});

const L = (c, t, k) => c + (t - c) * k;
function ticker() {
  /* reads */
  const vh = innerHeight, mid = vh / 2, y = scrollY;
  P.forEach((p) => {
    const r = p.el.getBoundingClientRect();
    p.ty = (r.top + r.height / 2 - mid) * p.sp;
  });
  /* writes */
  if (curOn) {
    cx = L(cx, mx, 0.22); cy = L(cy, my, 0.22);
    cursor.style.transform = `translate3d(${mx}px,${my}px,0)`;
    ring.style.transform = `translate3d(${cx}px,${cy}px,0)`;
  }
  P.forEach((p) => {
    p.y = L(p.y, p.ty, 0.12);
    p.el.style.transform = `${p.base}translate3d(0,${p.y.toFixed(2)}px,0)`;
  });
  T.forEach((t) => {
    t.rx = L(t.rx, t.trx, 0.14); t.ry = L(t.ry, t.try_, 0.14);
    t.el.style.transform = `perspective(900px) rotateX(${t.rx.toFixed(2)}deg) rotateY(${t.ry.toFixed(2)}deg)`;
  });
  M.forEach((m) => {
    m.dx = L(m.dx, m.tx, 0.18); m.dy = L(m.dy, m.ty, 0.18);
    m.el.style.transform = `translate3d(${m.dx.toFixed(1)}px,${m.dy.toFixed(1)}px,0)`;
  });
  const max = document.documentElement.scrollHeight - vh;
  prog.style.transform = `scaleX(${max > 0 ? Math.min(1, y / max) : 0})`;
  if (y > 240 && y > (ticker.y ?? 0) + 4) nav.classList.add('hide');
  else if (y < (ticker.y ?? 0) - 4) nav.classList.remove('hide');
  ticker.y = y;
  requestAnimationFrame(ticker);
}
if (!reduced) requestAnimationFrame(ticker);
else addEventListener('scroll', () => {
  const max = document.documentElement.scrollHeight - innerHeight;
  prog.style.transform = `scaleX(${max > 0 ? Math.min(1, scrollY / max) : 0})`;
}, { passive: true });

/* ── Contact ────────────────────────────────────────────────── */
$('#contactForm').addEventListener('submit', (ev) => {
  ev.preventDefault();
  const f = ev.target;
  if (CONFIG.email) {
    const body = encodeURIComponent(`Name: ${f.name.value}\nEmail: ${f.email.value}\n\n${f.project.value}`);
    location.href = `mailto:${CONFIG.email}?subject=${encodeURIComponent('Project — ' + f.name.value)}&body=${body}`;
  } else {
    toast('Inbox wiring soon — grabbing you to GitHub meanwhile ↗');
    setTimeout(() => window.open(CONFIG.github, '_blank'), 900);
  }
  f.reset();
});

/* ── Film player modal (v5) ─────────────────────────────── */
const pl = $('#player'), plV = $('#plVideo'), plT = $('#plTitle'), plC = $('#plClose');
function plOpen(src, title, wide) {
  plV.src = src;
  if (wide) plV.setAttribute('data-wide', '1'); else plV.removeAttribute('data-wide');
  plT.textContent = (title || 'FILM').toUpperCase();
  pl.classList.add('on');
  pl.setAttribute('aria-hidden', 'false');
  document.body.classList.add('locked');
  setTimeout(() => { plV.play().catch(() => {}); }, 80);
}
function plClose() {
  plV.pause();
  plV.removeAttribute('src');
  plV.load();
  pl.classList.remove('on');
  pl.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('locked');
}
$$('.work-card[data-src]').forEach((c) => c.addEventListener('click', () => {
  plOpen(c.dataset.src, c.dataset.title, c.dataset.wide === '1');
}));
plC.addEventListener('click', plClose);
pl.addEventListener('click', (e) => { if (e.target === pl) plClose(); });
addEventListener('keydown', (e) => { if (e.key === 'Escape' && pl.classList.contains('on')) plClose(); });

/* proof loop: play only while visible */
const ploop = $('#proofLoop');
if (ploop && !reduced) {
  new IntersectionObserver((en) => en.forEach((x) => {
    if (x.isIntersecting) ploop.play().catch(() => {}); else ploop.pause();
  }), { threshold: .3 }).observe(ploop);
}


boot();
