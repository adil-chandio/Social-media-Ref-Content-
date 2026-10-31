/* Adil Chandio — portfolio v3: single-rAF motion engine.
   One ticker drives cursor, parallax, tilt, glare, magnets, nav + progress.
   No scroll handlers, no competing transforms, no layout thrash → zero jerk. */
'use strict';
const CONFIG = {
  // Wire your real inbox here; until then the form points visitors to GitHub.
  email: 'workadilchandio@gmail.com',
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
  splash.classList.add('closing');
  setTimeout(() => {
    splash.classList.add('done');
    splash.classList.remove('closing');
    unlockScroll();
    sessionStorage.setItem(KEY, '1');
  }, reduced ? 0 : 480);
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
const mq860 = matchMedia('(max-width:860px)');
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
    if (!(mq860.matches && t.el.classList.contains('work-card'))) t.el.style.transform = `perspective(900px) rotateX(${t.rx.toFixed(2)}deg) rotateY(${t.ry.toFixed(2)}deg)`;
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

/* ── Film player modal (v5.2): local files + YouTube embeds ── */
const pl = $('#player'), plV = $('#plVideo'), plF = $('#plFrame'), plT = $('#plTitle'), plC = $('#plClose');
function plShow() { $$('.trailer').forEach((v) => { v.pause(); v.classList.remove('playing'); }); pl.classList.add('on'); pl.setAttribute('aria-hidden', 'false'); document.body.classList.add('locked'); }
function plHide() { pl.classList.remove('on'); pl.setAttribute('aria-hidden', 'true'); document.body.classList.remove('locked'); }
function plOpen(src, title) {
  plF.innerHTML = ''; plV.style.display = '';
  plV.src = src; plT.textContent = (title || 'FILM').toUpperCase(); plShow();
  setTimeout(() => { plV.play().catch(() => {}); }, 80);
}
function plOpenYt(id, title, wide) {
  plV.pause(); plV.removeAttribute('src'); plV.load(); plV.style.display = 'none';
  plF.innerHTML = '<iframe class="' + (wide ? 'yt-h' : 'yt-v') + '" src="https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0&playsinline=1" title="' + (title || 'Film') + '" frameborder="0" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>';
  plT.textContent = (title || 'FILM').toUpperCase(); plShow();
}
function plClose() { plV.pause(); plV.removeAttribute('src'); plV.load(); plF.innerHTML = ''; plHide(); }
$$('.work-card[data-src], .work-card[data-yt]').forEach((c) => c.addEventListener('click', () => {
  if (c.dataset.yt) plOpenYt(c.dataset.yt, c.dataset.title, c.dataset.wide === '1');
  else plOpen(c.dataset.src, c.dataset.title);
}));
plC.addEventListener('click', plClose);
pl.addEventListener('click', (e) => { if (e.target === pl) plClose(); });

/* proof loop: play only while visible */
const ploop = $('#proofLoop');
if (ploop && !reduced) {
  new IntersectionObserver((en) => en.forEach((x) => {
    if (x.isIntersecting) ploop.play().catch(() => {}); else ploop.pause();
  }), { threshold: .3 }).observe(ploop);
}


/* ── Receipts folder: fan stack → sliding cards (v5.2) ── */
const rcStack = $('#rcStack'), rcM = $('#rcModal'), rcmT = $('#rcmTrack'), rcmStage = $('#rcmStage'), rcmDots = $('#rcmDots'), rcmCount = $('#rcCount');
const rcCards = $$('.rcm-card');
let rci = 0;
rcCards.forEach((_, i) => {
  const b = document.createElement('button');
  b.className = 'rc-dot'; b.setAttribute('aria-label', 'Receipt ' + (i + 1));
  b.addEventListener('click', () => rcGo(i));
  rcmDots.appendChild(b);
});
function rcGo(i) {
  rci = Math.min(rcCards.length - 1, Math.max(0, i));
  const off = rcmStage.clientWidth + 18;
  rcmT.style.transform = 'translateX(' + (-rci * off) + 'px)';
  Array.from(rcmDots.children).forEach((d, k) => d.classList.toggle('on', k === rci));
  rcmCount.textContent = (rci + 1) + ' / ' + rcCards.length;
}
function rcOpen() { rcM.classList.add('on'); rcM.setAttribute('aria-hidden', 'false'); document.body.classList.add('locked'); rcGo(rci); }
function rcClose() { rcM.classList.remove('on'); rcM.setAttribute('aria-hidden', 'true'); document.body.classList.remove('locked'); }
rcStack.addEventListener('click', rcOpen);
$('#rcmClose').addEventListener('click', rcClose);
rcM.addEventListener('click', (e) => { if (e.target === rcM) rcClose(); });
$('#rcmPrev').addEventListener('click', () => rcGo(rci - 1));
$('#rcmNext').addEventListener('click', () => rcGo(rci + 1));
addEventListener('resize', () => { if (rcM.classList.contains('on')) rcGo(rci); });
let rx0 = null;
rcmStage.addEventListener('pointerdown', (e) => { rx0 = e.clientX; });
rcmStage.addEventListener('pointerup', (e) => {
  if (rx0 === null) return;
  const d = e.clientX - rx0; rx0 = null;
  if (d < -40) rcGo(rci + 1); else if (d > 40) rcGo(rci - 1);
});
addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  if (rcM.classList.contains('on')) rcClose();
});

/* ── v6 cinema pass ─────────────────────────────────────── */
/* per-char split for titles */
$$('[data-rv="chars"]').forEach((el) => {
  const txt = el.textContent; el.textContent = '';
  let i = 0;
  for (const ch of txt) {
    const sp = document.createElement('span');
    sp.className = 'ch'; sp.style.transitionDelay = (i * 26) + 'ms';
    if (ch === ' ') sp.innerHTML = '&nbsp;'; else sp.textContent = ch;
    el.appendChild(sp); i++;
  }
});
/* cursor context tags */
const cTag = $('#cursorTag');
if (cTag && fine) {
  document.addEventListener('mouseover', (e) => {
    const el = e.target.closest('[data-cursor]');
    if (el) { cTag.textContent = el.dataset.cursor; document.body.classList.add('cur-tag'); }
    else if (document.body.classList.contains('cur-tag')) document.body.classList.remove('cur-tag');
  }, { passive: true });
}
/* live Karachi clock */
const clk = $('#clk');
if (clk) {
  const fmt = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Karachi', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  const tick = () => { clk.textContent = fmt.format(new Date()); };
  tick(); setInterval(tick, 1000);
}
/* nav section spotlight */
const navAs = $$('.nav-links a');
const secIO = new IntersectionObserver((es) => es.forEach((en) => {
  if (en.isIntersecting) navAs.forEach((a) => a.classList.toggle('on', a.getAttribute('href') === '#' + en.target.id));
}), { rootMargin: '-42% 0px -52% 0px' });
$$('main section[id]').forEach((sec) => secIO.observe(sec));


$$('.work-card[data-src]').forEach((c) => {
  const v = c.querySelector('.trailer');
  if (!v || !fine) return;
  c.addEventListener('mouseenter', () => {
    if (!v.getAttribute('src')) v.src = c.dataset.src;
    v.play().then(() => v.classList.add('playing')).catch(() => {});
  });
  c.addEventListener('mouseleave', () => { v.pause(); v.classList.remove('playing'); });
});
if (!reduced) $$('.nav-links a, .foot-bar a').forEach((a) => a.addEventListener('mouseenter', () => scramble(a)));


/* ── v10 the letter: auto-reading scroll ────────────────── */
const lt = $('#letter'), ltS = $('#ltScroll'), ltCard = $('#letterCard');
let ltAuto = false, ltRaf = 0;
function ltStep() {
  if (!ltAuto || !lt.classList.contains('on')) { ltRaf = 0; return; }
  ltS.scrollTop += 0.65;
  if (ltS.scrollTop + ltS.clientHeight >= ltS.scrollHeight - 4) ltAuto = false;
  ltRaf = requestAnimationFrame(ltStep);
}
function ltOpen() {
  lt.classList.add('on'); lt.setAttribute('aria-hidden', 'false');
  document.body.classList.add('locked');
  ltS.scrollTop = 0; ltAuto = true;
  if (!ltRaf) ltRaf = requestAnimationFrame(ltStep);
}
function ltClose() {
  ltAuto = false; lt.classList.remove('on'); lt.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('locked');
}
if (ltCard) {
  ltCard.addEventListener('click', ltOpen);
  $('#ltClose').addEventListener('click', ltClose);
  lt.addEventListener('click', (e) => { if (e.target === lt) ltClose(); });
  ['wheel', 'touchstart', 'pointerdown'].forEach((ev) => ltS.addEventListener(ev, () => { ltAuto = false; }, { passive: true }));
  addEventListener('keydown', (e) => { if (e.key === 'Escape' && lt.classList.contains('on')) ltClose(); });
}


/* ── v12 maza: click ripple burst ───────────────────────── */
if (fine && !reduced) addEventListener('pointerdown', (e) => {
  const r = document.createElement('span');
  r.className = 'click-pop';
  r.style.left = e.clientX + 'px';
  r.style.top = e.clientY + 'px';
  document.body.appendChild(r);
  setTimeout(() => r.remove(), 620);
}, { passive: true });


/* ── v7 tabahi pass ─────────────────────────────────────── */
/* word-by-word lede split (preserves <em>) */
function wordify(el) {
  const nodes = Array.from(el.childNodes); el.textContent = '';
  let i = 0;
  const add = (n) => { n.classList.add('wd'); n.style.transitionDelay = (i * 34) + 'ms'; el.appendChild(n); el.appendChild(document.createTextNode(' ')); i++; };
  nodes.forEach((nd) => {
    if (nd.nodeType === 3) nd.textContent.split(/\s+/).filter(Boolean).forEach((w) => { const sp = document.createElement('span'); sp.textContent = w; add(sp); });
    else if (nd.nodeType === 1) add(nd);
  });
}
$$('[data-rv="words"]').forEach(wordify);
/* dot rail spy */
const dotAs = $$('.dots a');
const dotIO = new IntersectionObserver((es) => es.forEach((en) => {
  if (!en.isIntersecting) return;
  const id = en.target.classList.contains('hero') ? '#top' : '#' + en.target.id;
  dotAs.forEach((a) => a.classList.toggle('on', a.getAttribute('href') === id));
}), { rootMargin: '-42% 0px -52% 0px' });
const heroEl = $('.hero');
if (heroEl) dotIO.observe(heroEl);
$$('main section[id]').forEach((sec) => dotIO.observe(sec));
/* dark-section cursor spotlight */
let sRaf = 0, sEl = null, sx = 0, sy = 0;
if (fine) document.addEventListener('mousemove', (e) => {
  sx = e.clientX; sy = e.clientY;
  const el = e.target.closest ? e.target.closest('.section.dark') : null;
  if (el !== sEl) { if (sEl) { sEl.style.removeProperty('--sx'); sEl.style.removeProperty('--sy'); } sEl = el; }
  if (!el || sRaf) return;
  sRaf = requestAnimationFrame(() => { sRaf = 0; if (!sEl) return; const r = sEl.getBoundingClientRect(); sEl.style.setProperty('--sx', (sx - r.left) + 'px'); sEl.style.setProperty('--sy', (sy - r.top) + 'px'); });
}, { passive: true });
/* back-to-top FAB + progress ring */
const fab = $('#topFab'), fabFg = fab ? fab.querySelector('.fg') : null, FAB_C = 106.8;
let fR = 0;
function fabUp() {
  fR = 0;
  const y = scrollY || 0;
  const max = document.documentElement.scrollHeight - innerHeight;
  const p = max > 0 ? Math.min(1, y / max) : 0;
  if (fabFg) fabFg.style.strokeDashoffset = String(FAB_C * (1 - p));
  document.body.classList.toggle('fab-on', y > 600);
  const d0 = dotAs[0];
  if (d0 && y < 240) d0.classList.add('on');
}
addEventListener('scroll', () => { if (!fR) fR = requestAnimationFrame(fabUp); }, { passive: true });
if (fab) fab.addEventListener('click', () => scrollTo({ top: 0, behavior: 'smooth' }));
/* second clock (footer) */
const clk2 = $('#clk2');
if (clk && clk2) { const t2 = () => { clk2.textContent = clk.textContent; }; setInterval(t2, 1000); t2(); }


boot();

/* ── v14 reveal safety net (belt & braces over IO) ───────── */
if (!('IntersectionObserver' in window)) {
  $$('[data-rv]').forEach((el) => el.classList.add('in'));
} else {
  let rvRaf = 0;
  const rvNet = () => {
    rvRaf = 0;
    const vh = window.innerHeight;
    $$('[data-rv]:not(.in)').forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.top < vh * 0.92 && r.bottom > 0) { el.classList.add('in'); ioRv.unobserve(el); }
    });
  };
  const rvQueue = () => { if (!rvRaf) rvRaf = requestAnimationFrame(rvNet); };
  window.addEventListener('scroll', rvQueue, { passive: true });
  window.addEventListener('resize', rvQueue, { passive: true });
  setTimeout(rvNet, 1200);
  setTimeout(rvNet, 3500);
}

/* ── v16 anti-stuck watchdog: scroll kabhi lock nahi rahega ── */
const overlayUp = () =>
  (!gate.classList.contains('hidden')) ||
  (!splash.classList.contains('hidden') && !splash.classList.contains('done')) ||
  pl.classList.contains('on') || rcM.classList.contains('on') || lt.classList.contains('on');
let lockSince = 0;
setInterval(() => {
  const locked = document.body.classList.contains('locked');
  if (!locked) { lockSince = 0; return; }
  if (overlayUp()) { lockSince = Date.now(); return; }
  if (!lockSince) { lockSince = Date.now(); return; }
  if (Date.now() - lockSince > 5000) { document.body.classList.remove('locked'); lockSince = 0; }
}, 1000);
document.addEventListener('touchstart', () => {
  if (document.body.classList.contains('locked') && !overlayUp()) document.body.classList.remove('locked');
}, { passive: true });

/* ── v19: FREE PALESTINE wave delays + cloth flag ────────── */
$$('#fpTitle .ch').forEach((c, i) => c.style.setProperty('--wd', (i * 70) + 'ms'));
(function () {
  const cv = $('#flagCv'); if (!cv) return;
  const ctx = cv.getContext('2d');
  const FW = 560, FH = 360, flagW = 470, flagH = 280, ox = 56, oy = 44;
  const off = document.createElement('canvas'); off.width = flagW; off.height = flagH;
  const o = off.getContext('2d');
  const s = flagH / 3;
  o.fillStyle = '#000000'; o.fillRect(0, 0, flagW, s);
  o.fillStyle = '#f4f4f4'; o.fillRect(0, s, flagW, s);
  o.fillStyle = '#009736'; o.fillRect(0, s * 2, flagW, s);
  o.fillStyle = '#e2213b'; o.beginPath(); o.moveTo(0, 0); o.lineTo(flagW * 0.42, flagH / 2); o.lineTo(0, flagH); o.closePath(); o.fill();
  o.globalAlpha = .05;
  for (let i = 0; i < 900; i++) { o.fillStyle = Math.random() > .5 ? '#fff' : '#000'; o.fillRect(Math.random() * flagW, Math.random() * flagH, 1.4, 1.4); }
  o.globalAlpha = 1;
  const COLS = 56, cw = flagW / COLS;
  let t = 0, raf = 0, on = true;
  function frame() {
    raf = 0;
    ctx.clearRect(0, 0, FW, FH);
    const pg = ctx.createLinearGradient(ox - 10, 0, ox + 6, 0);
    pg.addColorStop(0, '#3a3a40'); pg.addColorStop(.5, '#8a8781'); pg.addColorStop(1, '#222226');
    ctx.fillStyle = pg; ctx.fillRect(ox - 7, oy - 26, 9, FH - oy - 16);
    ctx.beginPath(); ctx.arc(ox - 2.5, oy - 30, 7, 0, 7); ctx.fillStyle = '#d21f2b'; ctx.fill();
    for (let i = 0; i < COLS; i++) {
      const x = i * cw;
      const amp = 5 + 20 * (x / flagW);
      const ph = x * 0.018 - t;
      const y1 = Math.sin(ph) * amp + Math.sin(ph * 1.8 + 1.2) * amp * 0.35;
      const ph2 = (x + cw) * 0.018 - t;
      const amp2 = 5 + 20 * ((x + cw) / flagW);
      const y2 = Math.sin(ph2) * amp2 + Math.sin(ph2 * 1.8 + 1.2) * amp2 * 0.35;
      const slope = (y2 - y1) / cw;
      ctx.save();
      ctx.translate(ox + x, oy + y1);
      ctx.transform(1, slope * 0.9, 0, 1, 0, 0);
      ctx.drawImage(off, x, 0, cw + 0.6, flagH, 0, 0, cw + 0.6, flagH);
      const sh = Math.max(-1, Math.min(1, slope * 2.4));
      ctx.fillStyle = sh > 0 ? 'rgba(255,255,255,' + (sh * 0.16).toFixed(3) + ')' : 'rgba(0,0,0,' + (-sh * 0.34).toFixed(3) + ')';
      ctx.fillRect(0, 0, cw + 0.6, flagH);
      ctx.restore();
    }
    t += 0.045;
    if (on && !reduced) raf = requestAnimationFrame(frame);
  }
  new IntersectionObserver((en) => en.forEach((e) => {
    if (e.isIntersecting) { on = true; if (!raf && !reduced) raf = requestAnimationFrame(frame); }
    else { on = false; if (raf) { cancelAnimationFrame(raf); raf = 0; } }
  }), { threshold: .1 }).observe(cv);
  frame();
})();

/* ── v20: hero car scroll depth ─────────────────────────── */
(function () {
  const car = $('.hero-car'); if (!car) return;
  let q = 0;
  const mv = () => { q = 0; if (window.innerWidth <= 760) { car.style.transform = ''; return; } car.style.transform = 'translateY(' + Math.min(window.scrollY * 0.08, 150).toFixed(1) + 'px)'; };
  window.addEventListener('scroll', () => { if (!q) q = requestAnimationFrame(mv); }, { passive: true });
})();


/* ── v36: films butter-smooth — batched reads, lerped writes, IO-gated loop ── */
(function () {
  const grid = document.querySelector('.work-grid'); if (!grid) return;
  const cards = Array.prototype.slice.call(grid.children).filter(function (c) { return c.classList.contains('work-card'); });
  const plank = document.querySelector('.work-plank i');
  const mq = matchMedia('(max-width:860px)');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const st = cards.map(function (c) { return { c: c, py: 0, tpy: 0, px: 0, tpx: 0, rot: 0, trot: 0, sc: 1, tsc: 1 }; });
  let visible = false, running = false, raf = 0, wasM = mq.matches;
  function settle() {
    if (wasM === mq.matches) return;
    const toMob = mq.matches; wasM = toMob;
    for (const s of st) { if (!toMob) { s.c.style.transform = ''; } s.px = s.tpx = 0; s.rot = s.trot = 0; s.sc = s.tsc = 1; }
  }
  function frame() {
    if (!running) return;
    settle();
    const vh = innerHeight, mob = mq.matches;
    let gx = 0;
    if (mob) { const gr = grid.getBoundingClientRect(); gx = gr.left + gr.width / 2; }
    /* READ phase — all rects first, no writes interleaved */
    for (const s of st) {
      const r = s.c.getBoundingClientRect();
      if (mob) {
        const off = Math.max(-1.5, Math.min(1.5, (r.left + r.width / 2 - gx) / (innerWidth * 0.76)));
        s.trot = off * -7; s.tsc = 1 - Math.abs(off) * 0.05; s.tpx = off * 12; s.tpy = 0;
      } else if (r.bottom > -80 && r.top < vh + 80) {
        s.tpy = ((r.top + r.height / 2 - vh / 2) / vh) * -26;
      }
    }
    let sp = -1;
    if (mob) { const max = grid.scrollWidth - grid.clientWidth; sp = max > 0 ? grid.scrollLeft / max : 0; }
    /* WRITE phase — lerped, transform+vars only (compositor-friendly) */
    for (const s of st) {
      s.py += (s.tpy - s.py) * 0.14; s.px += (s.tpx - s.px) * 0.16;
      s.rot += (s.trot - s.rot) * 0.16; s.sc += (s.tsc - s.sc) * 0.16;
      if (mob) s.c.style.transform = 'perspective(900px) rotateY(' + s.rot.toFixed(2) + 'deg) scale(' + s.sc.toFixed(3) + ')';
      s.c.style.setProperty('--py', s.py.toFixed(1) + 'px');
      s.c.style.setProperty('--px', s.px.toFixed(1) + 'px');
    }
    if (plank && sp >= 0) plank.style.transform = 'translateX(' + (sp * 354).toFixed(1) + '%)';
    raf = requestAnimationFrame(frame);
  }
  function sync() {
    const want = visible && !reduced.matches;
    if (want && !running) { running = true; raf = requestAnimationFrame(frame); }
    else if (!want && running) { running = false; cancelAnimationFrame(raf); }
  }
  new IntersectionObserver(function (en) { visible = en[0].isIntersecting; sync(); }, { rootMargin: '25% 0px' }).observe(grid);
  addEventListener('resize', sync, { passive: true });
  if (reduced.addEventListener) reduced.addEventListener('change', sync);
  sync();
})();


/* ── v37: pause off-screen infinite animations (compositor relief) ── */
(function () {
  const els = document.querySelectorAll('.hero-car, .marquee, .sol-flag');
  if (!els.length || !('IntersectionObserver' in window)) return;
  const io = new IntersectionObserver(function (en) {
    en.forEach(function (e) { e.target.classList.toggle('idle', !e.isIntersecting); });
  }, { rootMargin: '12% 0px' });
  els.forEach(function (el) { io.observe(el); });
})();
