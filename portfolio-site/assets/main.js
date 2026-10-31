/* Adil Chandio — portfolio behaviour: intro film gate, splash, reveals, contact. */
'use strict';
const CONFIG = {
  // Wire your real inbox here; until then the form points visitors to GitHub.
  email: '',
  github: 'https://github.com/adil-chandio'
};
const KEY = 'ac_intro_seen';
const $ = (s) => document.querySelector(s);
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
  if (p && p.catch) p.catch(() => {           // autoplay blocked: let the user skip in
    toast('Tap SKIP to enter the site');
  });
}

function boot() {
  if (sessionStorage.getItem(KEY)) {          // same session → straight to the site
    gate.classList.add('hidden');
    splash.classList.add('hidden', 'done');
    unlockScroll();
  }                                          // else the gate is already on screen
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

/* ── Scroll reveals ──────────────────────────────────────────── */
const io = new IntersectionObserver((es) => {
  es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
}, { threshold: 0.15 });
document.querySelectorAll('[data-rv]').forEach((el) => io.observe(el));

/* ── Contact ─────────────────────────────────────────────────── */
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

boot();
