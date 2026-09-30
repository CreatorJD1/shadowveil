'use strict';
/* Pose driver (Clean room). Shows only authored images: the turnaround stills, the authored eye/hand stills
   composited where they align, and the talk clips. Crossfades use additive ('lighter') mixing of
   premultiplied pixels, so a blend is exactly (1-t)*A + t*B. Nothing is drawn, generated or mirrored. */
const $ = s => document.querySelector(s);
const W = 1365, H = 1739;
const stage = $('#stage'), sctx = stage.getContext('2d');
let P = null;                       // poses.json
const IMG = new Map();              // src -> HTMLImageElement
const COMP = new Map();             // cache key -> canvas (per-angle composite)
const opt = { eyes: true, hands: true, hair: true, sway: true, policy: 'auto', speed: 1, base: 0 };
const st = { phase: 'idle', t0: 0, from: 0, to: 0, dur: 0, angle: 0, target: null, auto: true, dir: 1, queue: [], talk: false, history: [], swayX: 0 };
const ease = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;   // ease-in-out (cubic)
const norm = a => ((a % 360) + 360) % 360;
const sdiff = (a, b) => { let d = norm(b - a); if (d > 180) d -= 360; return d; };     // shortest signed a->b

function load(src) {
  if (IMG.has(src)) return IMG.get(src);
  const p = new Promise((res, rej) => { const i = new Image(); i.decoding = 'async'; i.onload = () => res(i); i.onerror = () => rej(new Error('load ' + src)); i.src = src; });
  IMG.set(src, p); return p;
}
const stillOf = a => P.stills.find(s => s.angle === a);
const usable = () => P.stills.filter(s => s.consistent).map(s => s.angle).sort((a, b) => a - b);

/* ---------- consistency policy: which authored stills make up angle θ ---------- */
function resolve(theta, policy, dir) {
  const th = norm(theta), U = usable();
  let a0 = null, a1 = null;
  for (const a of U) if (a <= th + 1e-6) a0 = a;
  for (const a of U) if (a > th + 1e-6) { a1 = a; break; }
  if (a0 === null) a0 = U[U.length - 1];
  if (a1 === null) a1 = U[0];
  if (Math.abs(norm(th - a0)) < 1e-6) return { a: a0, b: a0, t: 0 };
  const span = norm(a1 - a0) || 360, t = norm(th - a0) / span;
  if (policy === 'hold' || (policy === 'auto' && span > 90)) return dir >= 0 ? { a: a0, b: a0, t: 0 } : { a: a1, b: a1, t: 0 };
  return { a: a0, b: a1, t };
}

/* ---------- per-angle composite: still + aligned authored overlays (+ hair skin-fill mask) ---------- */
function keyBlueMask(img, sc) {   // alpha from the blue chroma of an authored crop, eroded 2 px so no key fringe survives
  const w = Math.round(img.naturalWidth * sc), h = Math.round(img.naturalHeight * sc);
  const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d', { willReadFrequently: true });
  x.imageSmoothingQuality = 'high'; x.drawImage(img, 0, 0, w, h);
  const d = x.getImageData(0, 0, w, h), p = d.data, keep = new Uint8Array(w * h);
  for (let i = 0, j = 0; j < w * h; i += 4, j++) { const r = p[i], g = p[i + 1], b = p[i + 2]; keep[j] = !(b > 120 && b - r > 70 && b - g > 40); }
  for (let pass = 0; pass < 2; pass++) { const k2 = keep.slice(); for (let y = 1; y < h - 1; y++) for (let xx = 1; xx < w - 1; xx++) { const j = y * w + xx; if (k2[j] && !(k2[j - 1] && k2[j + 1] && k2[j - w] && k2[j + w])) keep[j] = 0; } }
  for (let j = 0; j < w * h; j++) if (!keep[j]) p[j * 4 + 3] = 0;
  for (let y = 0; y < h; y++) { p[(y * w) * 4 + 3] = 0; p[(y * w + w - 1) * 4 + 3] = 0; }
  x.putImageData(d, 0, 0); return c;
}
async function composite(a) {
  const key = `${a}|${opt.eyes}|${opt.hands}|${opt.hair}`;
  if (COMP.has(key)) return COMP.get(key);
  const pr = (async () => {
    const s = stillOf(a), base = await load(s.src);
    const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d', { willReadFrequently: true });
    x.drawImage(base, 0, 0);                                    // 1:1, rest spec canvas (head y=40, feet y=1681), no scaling
    const ovs = [];
    const e = s.overlays.eyes; if (opt.eyes && e && e.use) ovs.push(e);
    if (opt.hands) for (const hnd of s.overlays.hands || []) if (hnd.use) ovs.push(hnd);
    for (const o of ovs) {
      const m = keyBlueMask(await load(o.src), o.scale);
      // keep only where the still itself has pixels (overlay can never add outside her silhouette)
      const t = document.createElement('canvas'); t.width = m.width; t.height = m.height; const tx = t.getContext('2d');
      tx.drawImage(base, o.x, o.y, m.width, m.height, 0, 0, m.width, m.height); tx.globalCompositeOperation = 'source-in'; tx.drawImage(m, 0, 0);
      x.drawImage(t, o.x, o.y);
    }
    if (!opt.hair) { const d = x.getImageData(0, 0, W, H); let y0 = H, y1 = 0; const p = d.data;
      for (let y = 0; y < H; y++) for (let xx = 0; xx < W; xx++) if (p[(y * W + xx) * 4 + 3] > 16) { if (y < y0) y0 = y; if (y > y1) y1 = y; }
      applyPartMask(p, W, H, y0, y1, { hair: false, face: true, eyes: true, body: true }); x.putImageData(d, 0, 0); }
    return c;
  })();
  COMP.set(key, pr); return pr;
}

/* ---------- render ---------- */
const mix = document.createElement('canvas'); mix.width = W; mix.height = H; const mctx = mix.getContext('2d');
let lastBlend = null, drawing = false;
async function draw() {
  if (drawing) return; drawing = true;
  try {
    const r = resolve(st.angle, opt.policy, st.dir);
    const A = await composite(r.a), B = r.b !== r.a && r.t > 0 ? await composite(r.b) : null;
    mctx.globalCompositeOperation = 'copy'; mctx.globalAlpha = 1;
    if (!B) mctx.drawImage(A, 0, 0);
    else { mctx.globalAlpha = 1 - r.t; mctx.drawImage(A, 0, 0); mctx.globalCompositeOperation = 'lighter'; mctx.globalAlpha = r.t; mctx.drawImage(B, 0, 0); }
    mctx.globalAlpha = 1; mctx.globalCompositeOperation = 'source-over';
    sctx.clearRect(0, 0, W, H);
    sctx.drawImage(mix, Math.round(st.swayX), 0);             // idle sway = small horizontal offset only (no breathing / no scaling)
    lastBlend = r;
  } finally { drawing = false; }
}

/* ---------- state machine: idle -> turn -> hold -> drift -> idle ---------- */
const HOLD = 1400, IDLE = 2600;
const turnDur = d => Math.max(700, Math.abs(d) / 180 * 2400) / opt.speed;
function setPhase(phase, now, extra = {}) { st.phase = phase; st.t0 = now; Object.assign(st, extra); st.history.push({ phase, at: Math.round(now), angle: Math.round(norm(st.angle)) }); if (st.history.length > 60) st.history.shift(); }
function nextTarget() {
  const U = usable().filter(a => a !== opt.base);
  if (!st.queue.length) st.queue = U.slice();
  return st.queue.shift();
}
function goTo(target, now = performance.now()) {
  if (!stillOf(target)?.consistent) return false;            // inconsistent stills are never pose targets
  st.target = target; st.talk = false;
  const d = sdiff(st.angle, target); st.dir = Math.sign(d) || 1;
  setPhase('turn', now, { from: st.angle, to: st.angle + d, dur: turnDur(d) }); return true;
}
function step(now) {
  const el = now - st.t0;
  if (st.phase === 'idle') {
    st.angle = opt.base;
    if (st.auto && !st.talk && el > IDLE / opt.speed) goTo(nextTarget(), now);
  } else if (st.phase === 'turn' || st.phase === 'drift') {
    const k = Math.min(1, el / st.dur); st.angle = st.from + (st.to - st.from) * ease(k);
    if (k >= 1) { st.angle = norm(st.to);
      if (st.phase === 'turn') setPhase('hold', now);
      else setPhase('idle', now); }
  } else if (st.phase === 'hold') {
    if (el > HOLD / opt.speed) { const d = sdiff(st.angle, opt.base); st.dir = Math.sign(d) || -1;
      setPhase('drift', now, { from: st.angle, to: st.angle + d, dur: turnDur(d) * 1.6 }); }
  }
  // sway: only in idle (fades in/out), a few px
  const want = opt.sway && st.phase === 'idle' ? 1 : 0; st.swayAmt = (st.swayAmt || 0) + (want - (st.swayAmt || 0)) * 0.05;
  st.swayX = st.swayAmt * 3 * Math.sin(now / 1000 * 2 * Math.PI / 5.2);
}
let lastNow = 0;
function loop(now) {
  if (st.phase !== 'manual') step(now);
  draw(); ui(); talkTick();
  lastNow = now; requestAnimationFrame(loop);
}

/* ---------- talk (front only) with the Clean room white-flash skip ---------- */
const tv = document.createElement('video'); tv.muted = true; tv.playsInline = true; tv.loop = true; tv.preload = 'auto'; tv.crossOrigin = 'anonymous';
const tcv = $('#talkcv'), tctx = tcv.getContext('2d', { willReadFrequently: true }); let tHeld = null; st.flashSkips = 0;
const front = () => Math.abs(sdiff(0, st.angle)) <= P.talk.front_window_deg;
function talkKey() {   // same keying and white-flash test as the Clean room keyFrame()
  if (tv.readyState < 2) return;
  tctx.drawImage(tv, 0, 0, 768, 1168); const f = tctx.getImageData(0, 0, 768, 1168), p = f.data; let whiteN = 0;
  for (let i = 0; i < p.length; i += 4) { const r = p[i], g = p[i + 1], b = p[i + 2];
    if ((i & 63) === 0 && r > 245 && g > 245 && b > 245) whiteN++;
    const maxc = r > g ? r : g, d = b - maxc;
    if (maxc < 80 && b < 160) continue;
    if (b > 200 && r < 70 && g < 90 && d > 80) { p[i + 3] = 0; continue; }
    if (b > 175 && d > 60 && maxc > 50) { const keep = 255 - (d - 40) * 5; if (keep < p[i + 3]) p[i + 3] = keep < 0 ? 0 : keep; } }
  if (whiteN > 40 && tHeld) { tctx.putImageData(tHeld, 0, 0); st.flashSkips++; return; }
  tctx.putImageData(f, 0, 0); tHeld = f;
}
function talkTick() {
  const ok = front();
  $('#talkbtn').disabled = !ok && !st.talk;
  $('#talknote').textContent = ok ? (st.talk ? 'playing at 0° · auto paused' : 'front angle: ready') : 'available at 0° ±' + P.talk.front_window_deg + '° only';
  if (st.talk && !ok) stopTalk();
  if (st.talk) talkKey();
}
function startTalk() { if (!front()) return; st.talk = true; st.auto = false; $('#play').classList.remove('on');
  setPhase('talk', performance.now()); st.angle = 0; const src = P.talk.clips[+$('#talkclip').value]; if (tv.dataset.src !== src) { tv.src = src; tv.dataset.src = src; tHeld = null; }
  tv.play().catch(() => {}); $('#talkbtn').textContent = 'Talk ■'; }
function stopTalk() { st.talk = false; tv.pause(); $('#talkbtn').textContent = 'Talk ▶'; if (st.phase === 'talk') setPhase('idle', performance.now()); }
function qaStrip() {
  const k = ['speak', 'ask', 'laugh'][+$('#talkclip').value], ts = [0.4, 1.8, 3.2, 5.0];
  $('#qa').replaceChildren(...P.talk.qa[k].map((src, i) => { const im = new Image(); im.src = src; im.alt = k + ' ' + ts[i] + ' s'; im.title = im.alt;
    im.onclick = () => { if (!st.talk) startTalk(); if (st.talk) tv.currentTime = ts[i]; }; return im; }));
}

/* ---------- UI ---------- */
function badgeClass(s) { return s.audit === 'n/a' ? 'na' : s.consistent ? 'ok' : 'bad'; }
function buildUI() {
  $('#badges').replaceChildren(...P.stills.map(s => { const b = document.createElement('div'); b.className = 'badge ' + badgeClass(s); b.dataset.a = s.angle;
    const im = new Image(); im.src = s.src; im.alt = 'turn-' + s.angle; im.loading = 'eager';
    const t = document.createElement('span'); t.className = 't'; t.textContent = `${s.angle}° ${s.audit === 'n/a' ? '◌ n/a' : s.consistent ? '✓ blend' : '✗ held out'}`;
    b.title = s.note; b.append(im, t); b.onclick = () => { if (s.consistent) { st.auto = false; $('#play').classList.remove('on'); goTo(s.angle); } }; return b; }));
  $('#targets').replaceChildren(...P.stills.map(s => { const b = document.createElement('button'); b.textContent = s.angle + '°'; b.disabled = !s.consistent;
    b.title = s.consistent ? 'turn here, hold, drift back' : 'held out: ' + s.note; b.onclick = () => { st.auto = false; $('#play').classList.remove('on'); goTo(s.angle); }; return b; }));
  $('#base').replaceChildren(...P.stills.filter(s => s.consistent).map(s => { const o = document.createElement('option'); o.value = s.angle; o.textContent = s.angle + '°'; return o; }));
  const U = usable(), gaps = [];
  for (let i = 0; i < U.length; i++) { const a = U[i], b = U[(i + 1) % U.length]; const skipped = P.stills.filter(s => !s.consistent && norm(s.angle - a) > 0 && norm(s.angle - a) < norm(b - a || 360)).map(s => s.angle + '°'); if (skipped.length) gaps.push(`${a}°→${b}° skips ${skipped.join(', ')}`); }
  $('#policynote').innerHTML = `✓ = marks match turn-000 (1 under the amber eye, 2 under the green eye); ◌ = face turned away, marks not visible (expected, blendable); ✗ = mark count differs → held out: never a target and never blended. ${gaps.join('; ')}. <b>skip</b> blends straight between the nearest consistent neighbours; <b>hold</b> keeps the last consistent still until the next one is reached; <b>auto</b> blends gaps of 90° or less and holds across wider gaps (e.g. 0°→135°, where a front/back crossfade ghosts).`;
  $('#hairspec').textContent = P.hair.spec + ' — ' + P.hair.hide;
  const tl = $('#tl');
  for (const s of P.stills) { const m = document.createElement('div'); m.className = 'mk'; m.style.left = (s.angle / 360 * 100) + '%'; m.style.background = `var(--${badgeClass(s)})`;
    const sp = document.createElement('span'); sp.textContent = s.angle + '°'; sp.style.color = `var(--${badgeClass(s)})`; m.append(sp); tl.append(m); }
  const scrub = e => { const r = tl.getBoundingClientRect(); const a = Math.max(0, Math.min(359.9, (e.clientX - r.left) / r.width * 360));
    if (st.talk) stopTalk(); st.auto = false; $('#play').classList.remove('on'); st.dir = Math.sign(sdiff(st.angle, a)) || 1; if (st.phase !== 'manual') setPhase('manual', performance.now()); st.angle = a; };
  let down = false; tl.onpointerdown = e => { down = true; tl.setPointerCapture(e.pointerId); scrub(e); }; tl.onpointermove = e => down && scrub(e); tl.onpointerup = () => down = false;
  $('#play').onclick = () => { st.auto = !st.auto; $('#play').classList.toggle('on', st.auto); if (st.auto) { if (st.talk) stopTalk(); if (st.phase === 'manual') { const d = sdiff(st.angle, opt.base); setPhase('drift', performance.now(), { from: st.angle, to: st.angle + d, dur: turnDur(d) * 1.6 }); } } };
  $('#policy').onchange = e => { opt.policy = e.target.value; };
  $('#speed').onchange = e => { opt.speed = +e.target.value; };
  $('#base').onchange = e => { opt.base = +e.target.value; st.queue = []; if (st.phase === 'idle') st.angle = opt.base; };
  for (const [id, k] of [['lEyes', 'eyes'], ['lHands', 'hands'], ['lHair', 'hair'], ['lSway', 'sway']]) $('#' + id).onchange = e => { opt[k] = e.target.checked; };
  $('#talkbtn').onclick = () => st.talk ? stopTalk() : startTalk();
  $('#talkclip').onchange = () => { qaStrip(); if (st.talk) { stopTalk(); startTalk(); } };
  qaStrip();
}
let lastUi = '';
function ui() {
  const r = lastBlend || { a: 0, b: 0, t: 0 }; const near = P.stills.reduce((m, s) => Math.abs(sdiff(s.angle, st.angle)) < Math.abs(sdiff(m.angle, st.angle)) ? s : m);
  const txt = `angle ${norm(st.angle).toFixed(1)}°  phase ${st.phase}${st.target != null ? '  target ' + st.target + '°' : ''}\n` +
    (r.a === r.b || r.t === 0 ? `showing turn-${String(r.a).padStart(3, '0')}` : `blend turn-${String(r.a).padStart(3, '0')} ${(100 - r.t * 100).toFixed(0)}% + turn-${String(r.b).padStart(3, '0')} ${(r.t * 100).toFixed(0)}%`) +
    `  policy ${opt.policy}${Math.abs(st.swayX) > .05 ? '  sway ' + st.swayX.toFixed(1) + 'px' : ''}`;
  if (txt !== lastUi) { $('#hud').textContent = txt; lastUi = txt; }
  $('#ph').style.left = (norm(st.angle) / 360 * 100) + '%';
  document.querySelectorAll('#phases span[data-p]').forEach(s => s.classList.toggle('on', s.dataset.p === st.phase));
  document.querySelectorAll('.badge').forEach(b => b.classList.toggle('cur', +b.dataset.a === r.a || (+b.dataset.a === r.b && r.t > 0)));
  $('#blendinfo').textContent = `usable ${usable().map(a => a + '°').join(' ')} · held out ${P.stills.filter(s => !s.consistent).map(s => s.angle + '°').join(' ') || 'none'}`;
  if (near.angle !== ui.near) { ui.near = near.angle; const o = near.overlays;
    const notes = [`nearest still ${near.angle}° (${near.audit === 'n/a' ? 'marks not visible' : near.consistent ? 'consistent' : 'HELD OUT'}): ${near.note}`,
      `eyes: ${o.eyes.use ? 'authored eye still composited — ' : 'off — '}${o.eyes.why}`,
      `hands: ${(o.hands || []).map(h => (h.side ? h.side + ' ' : '') + (h.use ? 'composited — ' : 'off — ') + h.why).join('; ')}`,
      o.hands_strip ? `hands strip: ${o.hands_strip.why}` : '', `hair: ${o.hair.why}`].filter(Boolean);
    $('#layernote').replaceChildren(...notes.map(t => { const d = document.createElement('div'); d.textContent = '• ' + t; return d; }));
    const refs = [o.eyes.src, ...(o.hands || []).map(h => h.src), o.hands_strip?.src, o.hair.src].filter(Boolean);
    $('#refs').replaceChildren(...refs.map(src => { const im = new Image(); im.src = src; im.alt = src.split('/').pop(); im.title = src; return im; })); }
}

/* ---------- test hooks ---------- */
window.SVDriver = {
  get state() { return { phase: st.phase, angle: norm(st.angle), target: st.target, auto: st.auto, blend: lastBlend, history: st.history.slice(), talk: st.talk, flashSkips: st.flashSkips, opt: { ...opt } }; },
  goTo: a => goTo(a), setAuto: v => { st.auto = v; $('#play').classList.toggle('on', v); },
  scrubTo: a => { st.auto = false; st.dir = Math.sign(sdiff(st.angle, a)) || 1; setPhase('manual', performance.now()); st.angle = a; },
  setOpt: o => Object.assign(opt, o), resolve, startTalk, stopTalk, ready: false, drawNow: () => draw(), video: tv
};
fetch('poses.json', { cache: 'no-store' }).then(r => r.json()).then(async j => {
  P = j; opt.base = 0; st.angle = 0; buildUI();
  await Promise.all(P.stills.filter(s => s.consistent).map(s => composite(s.angle)));
  setPhase('idle', performance.now()); window.SVDriver.ready = true; requestAnimationFrame(loop);
});

/* ---------- hair hide: the Clean room skin-fill mask, copied verbatim from reference/grok_build/public/clean-room/index.html
   (applyPartMask; only change: layer visibility passed in). Authored-pixel masking: hair pixels inside the skull take the
   mean face-skin colour sampled from the same image, other hair pixels become transparent. ---------- */
function applyPartMask(p, w, h, y0, y1, layerOn) {
  const span = y1 - y0 + 1;
  const width = new Int16Array(h);
  for (let y = y0; y <= y1; y++) {
    let xL = -1;
    let xR = -1;
    const row = y * w * 4;
    for (let x = 0; x < w; x++) {
      if (p[row + x * 4 + 3] > 16) {
        if (xL < 0) xL = x;
        xR = x;
      }
    }
    if (xR > xL) width[y] = xR - xL;
  }
  const lo = y0 + (span * 0.08) | 0;
  const hi = Math.min(h - 1, y0 + (span * 0.34) | 0);
  let neck = -1;
  for (let y = hi; y > lo; y--) {
    let above = 0;
    for (let k = Math.max(y0, y - 36); k < y; k++) if (width[k] > above) above = width[k];
    let below = 0;
    for (let k = y + 1; k <= Math.min(h - 1, y + 48); k++) if (width[k] > below) below = width[k];
    if (above > 40 && width[y] > 8 && width[y] < above * 0.62 && below > width[y] * 1.7) {
      neck = y;
      break;
    }
  }
  if (neck < 0) return;
  let nsum = 0;
  let nn = 0;
  const nrow = neck * w * 4;
  for (let x = 0; x < w; x++) {
    if (p[nrow + x * 4 + 3] > 16) { nsum += x; nn++; }
  }
  if (!nn) return;
  const cx = nsum / nn | 0;
  const samples = [];
  for (let y = Math.max(y0, neck - 50); y < neck - 8; y++) if (width[y] > 0) samples.push(width[y]);
  samples.sort((a, b) => a - b);
  let faceW = samples.length ? samples[(samples.length * 0.8) | 0] : 80;
  if (faceW < 70) faceW = 70;
  const showHair = layerOn.hair !== false;
  const showFace = layerOn.face !== false;
  const showEyes = layerOn.eyes !== false;
  const showBody = layerOn.body !== false;
  const dark = new Uint8Array(w * h);
  const skin = new Uint8Array(w * h);
  for (let y = y0; y <= y1; y++) {
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      if (p[i + 3] < 16) continue;
      const r = p[i], g = p[i + 1], b = p[i + 2];
      const luma = (r + g + b) / 3;
      const id = y * w + x;
      if (r > 95 && g > 50 && r > b + 12 && g + 10 > b && r - g < 100 && luma > 80 && luma < 200) skin[id] = 1;
      else if (luma < 52) dark[id] = 1;
    }
  }
  const hair = new Uint8Array(w * h);
  const seen = new Uint8Array(w * h);
  const q = [];
  const seedHi = y0 + ((neck - y0) * 0.55) | 0;
  for (let y = y0; y < seedHi; y++) {
    const xA = Math.max(0, cx - faceW);
    const xB = Math.min(w - 1, cx + faceW);
    for (let x = xA; x <= xB; x++) {
      const id = y * w + x;
      if (dark[id]) { seen[id] = 1; q.push(id); }
    }
  }
  const limit = neck + (faceW * 0.25) | 0;
  const xReach = faceW * 1.15 | 0;
  for (let qi = 0; qi < q.length; qi++) {
    const id = q[qi];
    const y = (id / w) | 0;
    const x = id - y * w;
    if (y > limit || Math.abs(x - cx) > xReach) continue;
    hair[id] = 1;
    if (x + 1 < w) {
      const n = id + 1;
      if (!seen[n] && dark[n]) { seen[n] = 1; q.push(n); }
    }
    if (x > 0) {
      const n = id - 1;
      if (!seen[n] && dark[n]) { seen[n] = 1; q.push(n); }
    }
    if (y + 1 < h) {
      const n = id + w;
      if (!seen[n] && dark[n]) { seen[n] = 1; q.push(n); }
    }
    if (y > 0) {
      const n = id - w;
      if (!seen[n] && dark[n]) { seen[n] = 1; q.push(n); }
    }
  }
  const crown = neck - (faceW * 1.35) | 0;
  const chin = neck - 2;
  const cy = (crown + chin) >> 1;
  const rx = faceW * 0.62 | 0;
  const ry = Math.max(8, (chin - crown) >> 1);
  let sr = 0, sg = 0, sb = 0, sn = 0;
  for (let y = Math.max(0, cy); y < Math.max(cy, chin - 2); y++) {
    for (let x = Math.max(0, cx - (rx >> 1)); x <= Math.min(w - 1, cx + (rx >> 1)); x++) {
      const id = y * w + x;
      if (!skin[id]) continue;
      const i = id * 4;
      sr += p[i]; sg += p[i + 1]; sb += p[i + 2]; sn++;
    }
  }
  const cr = sn ? sr / sn | 0 : 176;
  const cg = sn ? sg / sn | 0 : 116;
  const cb = sn ? sb / sn | 0 : 74;
  const eye = new Uint8Array(w * h);
  const rad = 2;
  for (let y = Math.max(0, crown); y <= Math.min(h - 1, chin); y++) {
    for (let x = Math.max(0, cx - rx - 6); x <= Math.min(w - 1, cx + rx + 6); x++) {
      const i = (y * w + x) * 4;
      if (p[i + 3] < 16) continue;
      const r = p[i], g = p[i + 1], b = p[i + 2];
      const maxc = r > g ? r : g;
      const minc = r < g ? (r < b ? r : b) : (g < b ? g : b);
      const luma = (r + g + b) / 3;
      if (!(r > 198 && g > 180 && b > 155 && maxc - minc < 58 && luma > 170)) continue;
      for (let yy = Math.max(0, y - rad); yy <= Math.min(h - 1, y + rad); yy++) {
        for (let xx = Math.max(0, x - rad); xx <= Math.min(w - 1, x + rad); xx++) {
          const j = (yy * w + xx) * 4;
          if (p[j + 3] < 16) continue;
          const rr = p[j], gg = p[j + 1], bb = p[j + 2];
          const lum = (rr + gg + bb) / 3;
          if (lum < 70) continue;
          const mx = rr > gg ? rr : gg;
          const mn = rr < gg ? (rr < bb ? rr : bb) : (gg < bb ? gg : bb);
          const mx2 = mx > bb ? mx : bb;
          const scl = rr > 198 && gg > 180 && bb > 155 && mx2 - mn < 58;
          const amber = rr > 155 && rr > gg + 8 && bb < 145 && gg - bb > 20 && mx2 - mn > 30;
          const green = gg > rr + 8 && gg > bb + 4 && gg > 75 && mx2 - mn > 25;
          if (scl || amber || green) eye[yy * w + xx] = 1;
        }
      }
    }
  }
  const rx2 = rx * rx || 1;
  const ry2 = ry * ry || 1;
  for (let y = y0; y <= y1; y++) {
    for (let x = 0; x < w; x++) {
      const id = y * w + x;
      const i = id * 4;
      if (p[i + 3] < 16) continue;
      const inSkull = ((y - cy) * (y - cy)) / ry2 + ((x - cx) * (x - cx)) / rx2 <= 1;
      const isHair = hair[id] === 1;
      const isEye = eye[id] === 1;
      const isFace = skin[id] === 1 && y <= chin && y >= crown - 8 && Math.abs(x - cx) < rx + 10;
      if (!showEyes && isEye) { p[i + 3] = 0; continue; }
      if (!showHair && isHair) {
        if (inSkull) { p[i] = cr; p[i + 1] = cg; p[i + 2] = cb; }
        else p[i + 3] = 0;
        continue;
      }
      if (!showFace && isFace && !isHair && !isEye) { p[i + 3] = 0; continue; }
      if (!showBody && !isHair && !isFace && !isEye) p[i + 3] = 0;
    }
  }
}
