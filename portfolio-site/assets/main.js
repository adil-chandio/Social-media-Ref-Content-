/* Adil Chandio — portfolio v2: intro film gate + motion layer (cursor, parallax,
   magnetic buttons, tilt, scramble, counters, reveals, nav hide, progress). */
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
const toastEl = $('#toast');
let toastT;

function toast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  clearTimeout(toastT);
  toastT = setTimeout(() => toastEl.classList.remove('show'), 3200);
}

/* ── Intro film flow ─────────────────────────────────────────── */
function unlockScroll() { document.body.classList.remove('locked'); }
function lockScroll() { document.body.classList.add('locked'); }

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
  if (p && p.then) p.then(() => splash.classList.add('open')).catch(() => {
    splash.classList.add('open');
    toast('Tap SKIP to enter the site');
  });
}

function boot() {
  if (sessionStorage.getItem(KEY)) {          // same session → straight to the site
    gate.classList.add('hidden');
    splash.classList.add('hidden', 'done');
    unlockScroll();
  } else {
    requestAnimationFrame(() => gate.querySelector('.gate-name').classList.add('in'));
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
film.addEventListener('click', endIntro);     // tap the film itself to skip (mobile)

/* ── Scroll reveals + counters + scramble ────────────────────── */
const GLYPHS = '█▓▒░<>/\\|=+*·01';
function scramble(el) {
  const final = el.dataset.txt || (el.dataset.txt = el.textContent);
  let f = 0;
  const total = 18;
  const id = setInterval(() => {
    f++;
    el.textContent = final.split('').map((ch, i) => {
      if (ch === ' ' || i < (f / total) * final.length) return ch;
      return GLYPHS[(Math.random() * GLYPHS.length) | 0];
    }).join('');
    if (f >= total) { clearInterval(id); el.textContent = final; }
  }, 34);
}
function countUp(el) {
  const target = +el.dataset.count, pad = +(el.dataset.pad || 0);
  const t0 = performance.now(), dur = 1100;
  const fmt = (v) => String(v).padStart(pad, '0');
  (function step(t) {
    const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
    el.textContent = fmt(Math.round(target * e));
    if (k < 1) requestAnimationFrame(step);
  })(t0);
}
const io = new IntersectionObserver((es) => {
  es.forEach((e) => {
    if (!e.isIntersecting) return;
    e.target.classList.add('in');
    if (e.target.hasAttribute('data-scramble') && !reduced) scramble(e.target);
    e.target.querySelectorAll?.('[data-count]') ;
    if (e.target.matches('[data-count]')) countUp(e.target);
    e.target.querySelectorAll('[data-count]').forEach((c) => { if (!c.dataset.done) { c.dataset.done = 1; countUp(c); } });
    io.unobserve(e.target);
  });
}, { threshold: 0.18 });
$$('[data-rv],[data-count]').forEach((el) => io.observe(el));

/* ── Motion loop: cursor lerp, parallax, progress, nav hide ──── */
const cursor = $('#cursor'), ring = $('#cursorRing'), prog = $('#prog'), nav = $('#nav');
const px = $$('[data-px]');
let mx = innerWidth / 2, my = innerHeight / 2, rx = mx, ry = my, lastY = scrollY, ticking = false;

addEventListener('mousemove', (e) => { mx = e.clientX; my = e.clientY; }, { passive: true });
$$('a,button,.work-card,.sk').forEach((el) => {
  el.addEventListener('mouseenter', () => document.body.classList.add('cur-hot'));
  el.addEventListener('mouseleave', () => document.body.classList.remove('cur-hot'));
});

function loop() {
  rx += (mx - rx) * 0.18; ry += (my - ry) * 0.18;
  if (cursor) { cursor.style.transform = `translate(${mx}px,${my}px)`; }
  if (ring) { ring.style.transform = `translate(${rx}px,${ry}px)`; }
  requestAnimationFrame(loop);
}

function onScroll() {
  const y = scrollY;
  const max = document.documentElement.scrollHeight - innerHeight;
  prog.style.transform = `scaleX(${max > 0 ? y / max : 0})`;
  if (y > 240 && y > lastY + 4) nav.classList.add('hide');
  else if (y < lastY - 4) nav.classList.remove('hide');
  lastY = y;
  if (!reduced) {
    const mid = innerHeight / 2;
    px.forEach((el) => {
      const r = el.getBoundingClientRect();
      const off = (r.top + r.height / 2 - mid) * parseFloat(el.dataset.px);
      el.style.transform = `translate3d(0,${off.toFixed(1)}px,0)` + (el.classList.contains('portrait-clip') ? '' : '');
    });
  }
  ticking = false;
}
addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });

/* portrait img keeps its zoom scale while parallaxing */
(function patchPortrait() {
  const img = document.querySelector('.portrait img[data-px]');
  if (!img) return;
  const base = 'scale(1.12) ';
  const obs = new MutationObserver(() => {});
  obs.disconnect();
  const set = () => {
    const r = img.getBoundingClientRect();
    const off = (r.top + r.height / 2 - innerHeight / 2) * parseFloat(img.dataset.px);
    img.style.transform = base + `translate3d(0,${off.toFixed(1)}px,0)`;
  };
  addEventListener('scroll', () => requestAnimationFrame(set), { passive: true });
  set();
  img.removeAttribute('data-px');
})();

/* ── Magnetic buttons ────────────────────────────────────────── */
if (fine && !reduced) {
  $$('.magnet').forEach((el) => {
    el.addEventListener('mousemove', (e) => {
      const r = el.getBoundingClientRect();
      const dx = (e.clientX - r.left - r.width / 2) * 0.28;
      const dy = (e.clientY - r.top - r.height / 2) * 0.34;
      el.style.transform = `translate(${dx.toFixed(1)}px,${dy.toFixed(1)}px)`;
    });
    el.addEventListener('mouseleave', () => { el.style.transform = ''; });
  });
}

/* ── Skill hover glow + work card tilt ───────────────────────── */
if (fine) {
  $$('.sk').forEach((li) => li.addEventListener('mousemove', (e) => {
    const r = li.getBoundingClientRect();
    li.style.setProperty('--mx', (e.clientX - r.left) + 'px');
    li.style.setProperty('--my', (e.clientY - r.top) + 'px');
  }));
  $$('[data-tilt]').forEach((card) => {
    const fig = card.querySelector('figure');
    card.addEventListener('mousemove', (e) => {
      const r = card.getBoundingClientRect();
      const pxr = (e.clientX - r.left) / r.width - 0.5;
      const pyr = (e.clientY - r.top) / r.height - 0.5;
      fig.style.setProperty('--ry', (pxr * 7).toFixed(2) + 'deg');
      fig.style.setProperty('--rx', (-pyr * 7).toFixed(2) + 'deg');
    });
    card.addEventListener('mouseleave', () => {
      fig.style.setProperty('--ry', '0deg'); fig.style.setProperty('--rx', '0deg');
    });
  });
}

if (fine && !reduced) { document.body.classList.add('cur'); requestAnimationFrame(loop); }
onScroll();
boot();
