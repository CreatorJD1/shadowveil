'use strict';
/* Pose driver (Clean room) v2 — plays the authored A-pose turn (reference/apose_turn f001–f232) frame by frame.
   The generated turnaround stills (clean-room/layers/rotation/turn-*.png) are NOT used anywhere.
   During the turn only the authored frame is shown (eyes, mouth, hands, hair are baked in); the live rig parts
   (rig/index.html?view=…, embedded read-only) are composited only at the handoff frames, crossfaded on the matched
   scale/offset. Crossfades are exact (1-w)·A + w·B ('lighter' on premultiplied pixels). Nothing is drawn, generated
   or mirrored; keying + blue despill only change existing pixels. */
const $ = s => document.querySelector(s);
const W = 1365, H = 1739, FW = 768, FH = 1168;
const stage = $('#stage'), sctx = stage.getContext('2d');
let P = null, FR = null, LOOP = 232;
const opt = { speed: 1, sway: true, base: 1, despill: true };
const st = { phase: 'loading', t0: 0, fromF: 1, toF: 1, dist: 0, dur: 0, pos: 1, target: null, auto: true, queue: [], talk: false, history: [], swayX: 0, swayAmt: 0, w: 0, wFrom: 0, wTo: 0, wT0: 0, handoffView: null, flashSkips: 0, handoffs: 0 };
const ease = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const wrapF = p => { const n = LOOP; let q = ((p - 1) % n + n) % n; return q + 1; };           // 1..LOOP (float), f232 wraps to f001
const fdiff = (a, b) => { const n = LOOP; let d = ((b - a) % n + n) % n; if (d > n / 2) d -= n; return d; };
const handoffAt = f => P.handoffs.find(h => h.frame === f);

/* ---------- frames: load, key (Clean room rules), hair-edge despill ---------- */
const IMG = new Map(), KEYED = new Map(), KEY_ORDER = [];
function loadImg(src) { if (!IMG.has(src)) IMG.set(src, new Promise((res, rej) => { const i = new Image(); i.decoding = 'async'; i.onload = () => res(i); i.onerror = () => rej(new Error(src)); i.src = src; })); return IMG.get(src); }
async function keyed(f) {
  const k = f + '|' + opt.despill; if (KEYED.has(k)) return KEYED.get(k);
  const pr = (async () => {
    const im = await loadImg(FR[f - 1].src);
    const c = document.createElement('canvas'); c.width = FW; c.height = FH; const x = c.getContext('2d', { willReadFrequently: true });
    x.drawImage(im, 0, 0); const d = x.getImageData(0, 0, FW, FH), p = d.data;
    for (let i = 0; i < p.length; i += 4) { const r = p[i], g = p[i + 1], b = p[i + 2]; const maxc = r > g ? r : g, dd = b - maxc;
      if (maxc < 80 && b < 160) continue;
      if (b > 200 && r < 70 && g < 90 && dd > 80) { p[i + 3] = 0; continue; }
      if (b > 175 && dd > 60 && maxc > 50) { const keep = 255 - (dd - 40) * 5; if (keep < p[i + 3]) p[i + 3] = keep < 0 ? 0 : keep; } }
    if (opt.despill) {   // colour-correct existing pixels in a 3 px band next to the key: clamp blue spill
      const a = new Uint8Array(FW * FH); for (let j = 0; j < FW * FH; j++) a[j] = p[j * 4 + 3] < 250 ? 1 : 0;
      let band = a.slice(); for (let pass = 0; pass < 3; pass++) { const b2 = band.slice(); for (let y = 1; y < FH - 1; y++) for (let xx = 1; xx < FW - 1; xx++) { const j = y * FW + xx; if (!b2[j] && (b2[j - 1] || b2[j + 1] || b2[j - FW] || b2[j + FW])) band[j] = 1; } }
      for (let j = 0; j < FW * FH; j++) { if (!band[j]) continue; const i = j * 4; if (p[i + 3] === 0) continue; const mx = Math.max(p[i], p[i + 1]) + 8; if (p[i + 2] > mx) p[i + 2] = mx; }
    }
    x.putImageData(d, 0, 0); return c;
  })();
  KEYED.set(k, pr); KEY_ORDER.push(k); while (KEY_ORDER.length > 48) KEYED.delete(KEY_ORDER.shift());
  return pr;
}

/* ---------- live parts: the rig at each rest view (embedded read-only; auto blink/talk kept off) ---------- */
const RIG = {};
function rigFrame(view) {
  if (RIG[view]) return RIG[view];
  const fr = document.createElement('iframe'); fr.src = '../../rig/index.html?view=' + view; fr.title = 'live rig ' + view; fr.className = 'rigsrc';
  $('#rigs').append(fr);
  const r = RIG[view] = { fr, ready: false, canvas: null };
  fr.addEventListener('load', () => { const poll = () => { try { const d = fr.contentDocument, c = d.getElementById('c');
      const auto = d.getElementById('auto'); if (auto && auto.checked) auto.click();          // keep auto (blink / talk / springs input) off
      if (c && c.width === W) { const px = c.getContext('2d').getImageData(0, 0, W, H).data; let n = 0; for (let i = 3; i < px.length; i += 4000) if (px[i]) n++; if (n > 20) { r.canvas = c; r.ready = true; return; } } } catch (e) {}
    setTimeout(poll, 250); }; poll(); });
  return r;
}
function freezeRig(view) { const r = RIG[view]; if (!r || !r.ready) return; try { const auto = r.fr.contentDocument.getElementById('auto'); if (auto && auto.checked) auto.click(); } catch (e) {} }

/* ---------- render ---------- */
const mix = document.createElement('canvas'); mix.width = W; mix.height = H; const mctx = mix.getContext('2d');
let drawing = false, last = null;
async function draw() {
  if (drawing) return; drawing = true;
  try {
    const f = Math.round(wrapF(st.pos)), m = FR[f - 1], img = await keyed(f);
    const ho = st.handoffView && RIG[st.handoffView] && RIG[st.handoffView].ready ? RIG[st.handoffView] : null, w = ho ? st.w : 0;
    mctx.globalCompositeOperation = 'copy'; mctx.globalAlpha = 1 - w; mctx.imageSmoothingQuality = 'high';
    mctx.setTransform(m.scale, 0, 0, m.scale, m.dx, m.dy); mctx.drawImage(img, 0, 0); mctx.setTransform(1, 0, 0, 1, 0, 0);
    if (w > 0) { mctx.globalCompositeOperation = 'lighter'; mctx.globalAlpha = w; mctx.drawImage(ho.canvas, 0, 0); }
    mctx.globalAlpha = 1; mctx.globalCompositeOperation = 'source-over';
    sctx.clearRect(0, 0, W, H); sctx.drawImage(mix, Math.round(st.swayX), 0);   // idle sway: small x offset only
    last = { frame: f, w, view: ho ? st.handoffView : null };
  } finally { drawing = false; }
}

/* ---------- state machine: rest(idle) -> turn -> hold -> drift -> rest ---------- */
const HOLD = 1400, IDLE = 2600, XF = 80;   // whole-frame <-> whole-live-view crossfade at a handoff (~80 ms)
function setPhase(phase, now, extra = {}) { st.phase = phase; st.t0 = now; Object.assign(st, extra); st.history.push({ phase, at: Math.round(now), frame: Math.round(wrapF(st.pos)) }); if (st.history.length > 80) st.history.shift(); }
function fadeTo(w, now) { st.wFrom = st.w; st.wTo = w; st.wT0 = now; }
function arriveAt(f, now) {           // hand back to the live parts only on a handoff frame
  const h = handoffAt(f);
  if (h) { st.handoffView = h.view; rigFrame(h.view); freezeRig(h.view); fadeTo(1, now); st.handoffs++; } else { fadeTo(0, now); }
}
function goTo(f, now = performance.now()) {
  if (!P.targets.includes(f) && !handoffAt(f)) return false;
  if (st.talk) stopTalk();
  st.target = f; const d = fdiff(wrapF(st.pos), f);
  fadeTo(0, now);                                            // live parts out before the frames move
  setPhase('turn', now, { fromF: wrapF(st.pos), dist: d, dur: Math.max(500, Math.abs(d) / 24 * 1000) / opt.speed, delay: st.w > 0 ? XF + 20 : 0 }); return true;
}
function nextTarget() { const T = P.targets.filter(f => f !== opt.base); if (!st.queue.length) st.queue = T.slice(); return st.queue.shift(); }
function step(now) {
  const el = now - st.t0;
  if (st.phase === 'idle') { st.pos = opt.base; if (st.auto && !st.talk && el > IDLE / opt.speed) goTo(nextTarget(), now); }
  else if (st.phase === 'turn' || st.phase === 'drift') {
    const e2 = el - (st.delay || 0);
    if (e2 > 0) { const k = Math.min(1, e2 / st.dur); st.pos = wrapF(st.fromF + st.dist * ease(k));
      if (k >= 1) { st.pos = Math.round(wrapF(st.fromF + st.dist));
        if (st.phase === 'turn') { setPhase('hold', now); arriveAt(st.pos, now); }
        else { setPhase('idle', now); arriveAt(st.pos, now); } } }
  } else if (st.phase === 'hold') {
    if (st.auto && el > HOLD / opt.speed) { const d = fdiff(st.pos, opt.base); fadeTo(0, now);
      setPhase('drift', now, { fromF: st.pos, dist: d, dur: Math.max(700, Math.abs(d) / 24 * 1000) * 1.5 / opt.speed, delay: st.w > 0 ? XF : 0 }); }
  }
  const k = Math.min(1, (now - st.wT0) / XF); st.w = st.wFrom + (st.wTo - st.wFrom) * ease(k);
  const want = opt.sway && st.phase === 'idle' && !st.talk ? 1 : 0; st.swayAmt += (want - st.swayAmt) * 0.05;
  st.swayX = st.swayAmt * 3 * Math.sin(now / 1000 * 2 * Math.PI / 5.2);
}
function loop(now) { if (st.phase !== 'manual') step(now); else { const k = Math.min(1, (now - st.wT0) / XF); st.w = st.wFrom + (st.wTo - st.wFrom) * ease(k); st.swayX = 0; }
  draw(); ui(); talkTick(); requestAnimationFrame(loop); }

/* ---------- talk (front rest at f001 only) with the Clean room white-flash skip ---------- */
const tv = document.createElement('video'); tv.muted = true; tv.playsInline = true; tv.loop = true; tv.preload = 'auto';
const tcv = $('#talkcv'), tctx = tcv.getContext('2d', { willReadFrequently: true }); let tHeld = null;
const frontRest = () => Math.round(wrapF(st.pos)) === 1 && (st.phase === 'idle' || st.phase === 'talk' || st.phase === 'hold' || st.phase === 'manual');
function talkKey() {
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
function talkTick() { const ok = frontRest(); $('#talkbtn').disabled = !ok && !st.talk;
  $('#talknote').textContent = ok ? (st.talk ? 'playing at f001 (front) · auto paused' : 'front rest: ready') : 'only while resting at f001 (front)';
  if (st.talk && !ok) stopTalk(); if (st.talk) talkKey(); }
function startTalk() { if (!frontRest()) return; st.talk = true; st.auto = false; $('#play').classList.remove('on'); setPhase('talk', performance.now());
  const src = P.talk.clips[+$('#talkclip').value]; if (tv.dataset.src !== src) { tv.src = src; tv.dataset.src = src; tHeld = null; } tv.play().catch(() => {}); $('#talkbtn').textContent = 'Talk ■'; }
function stopTalk() { st.talk = false; tv.pause(); $('#talkbtn').textContent = 'Talk ▶'; if (st.phase === 'talk') setPhase('idle', performance.now()); }
function qaStrip() { const k = ['speak', 'ask', 'laugh'][+$('#talkclip').value], ts = [0.4, 1.8, 3.2, 5.0];
  $('#qa').replaceChildren(...P.talk.qa[k].map((src, i) => { const im = new Image(); im.src = src; im.alt = k + ' ' + ts[i] + ' s'; im.title = im.alt; im.onclick = () => { if (!st.talk) startTalk(); if (st.talk) tv.currentTime = ts[i]; }; return im; })); }

/* ---------- manual dial ---------- */
function scrubTo(f, release = false) {
  if (st.talk) stopTalk(); st.auto = false; $('#play').classList.remove('on');
  f = Math.max(1, Math.min(LOOP, Math.round(f)));
  if (release && P.no_hold.includes(f)) f += (f >= st.pos ? 1 : -1);      // never rest on f057 / f164
  if (st.phase !== 'manual') setPhase('manual', performance.now());
  if (f !== Math.round(st.pos)) { fadeTo(0, performance.now()); }
  st.pos = f; if (release) arriveAt(f, performance.now());
}

/* ---------- UI ---------- */
function buildUI() {
  const lab = f => { const a = P.anchors.find(x => x.frame === f); const h = handoffAt(f); return `f${String(f).padStart(3, '0')}${a ? ' ' + a.angle + '°' : ''}${h ? ' · ' + h.view : ''}`; };
  $('#targets').replaceChildren(...P.targets.map(f => { const b = document.createElement('button'); b.textContent = lab(f); b.title = handoffAt(f) ? 'handoff frame: live parts return here' : 'hold on the authored frame (live parts stay hidden)'; b.onclick = () => { st.auto = false; $('#play').classList.remove('on'); goTo(f); }; return b; }));
  $('#base').replaceChildren(...P.handoffs.map(h => { const o = document.createElement('option'); o.value = h.frame; o.textContent = lab(h.frame); return o; }));
  const dial = $('#dial'); dial.max = LOOP; dial.oninput = e => scrubTo(+e.target.value); dial.onchange = e => scrubTo(+e.target.value, true);
  const tl = $('#tl');
  for (const a of P.anchors) if (a.frame <= LOOP) { const m = document.createElement('div'); m.className = 'mk' + (handoffAt(a.frame) ? ' ho' : ''); m.style.left = ((a.frame - 1) / (LOOP - 1) * 100) + '%'; const sp = document.createElement('span'); sp.textContent = lab(a.frame); m.append(sp); tl.append(m); }
  for (const f of P.no_hold) { const m = document.createElement('div'); m.className = 'mk nh'; m.style.left = ((f - 1) / (LOOP - 1) * 100) + '%'; m.title = 'f' + f + ': no hold (hand blends into hip)'; tl.append(m); }
  for (const fr of FR.slice(0, LOOP)) { if (fr.marks.consistent === 'false' || fr.marks.consistent === 'uncertain') { const t = document.createElement('div'); t.className = 'bm ' + fr.marks.consistent; t.style.left = ((fr.f - 1) / (LOOP - 1) * 100) + '%'; t.title = `f${fr.f} beauty-mark audit: ${fr.marks.consistent} (${fr.marks.confidence}) ${fr.marks.positions || ''}`; tl.append(t); } }
  $('#play').onclick = () => { st.auto = !st.auto; $('#play').classList.toggle('on', st.auto); if (st.auto) { if (st.talk) stopTalk(); if (st.phase === 'manual') { const d = fdiff(st.pos, opt.base); fadeTo(0, performance.now()); setPhase('drift', performance.now(), { fromF: st.pos, dist: d, dur: Math.max(700, Math.abs(d) / 24 * 1000) * 1.5 / opt.speed, delay: 0 }); } } };
  $('#speed').onchange = e => { opt.speed = +e.target.value; };
  $('#base').onchange = e => { opt.base = +e.target.value; st.queue = []; };
  $('#lSway').onchange = e => { opt.sway = e.target.checked; };
  $('#lDespill').onchange = e => { opt.despill = e.target.checked; };
  $('#talkbtn').onclick = () => st.talk ? stopTalk() : startTalk();
  $('#talkclip').onchange = () => { qaStrip(); if (st.talk) { stopTalk(); startTalk(); } };
  $('#rules').innerHTML = `<b>Turn source:</b> reference/apose_turn f001–f${LOOP} (authored A-pose turn), loop wraps f${LOOP}→f001 (f233–f241 settle skipped). Generated turnaround stills are not used. <b>Fit:</b> ${P.fit_source}. <b>Handoffs</b> (live parts return, crossfade ${XF} ms): ${P.handoffs.map(h => 'f' + String(h.frame).padStart(3, '0') + ' ' + h.view + ' (bun z' + h.bun_z + ')').join(', ')}. <b>Hidden during the turn:</b> eyes ${P.hidden_during_turn.eyes}; mouth ${P.hidden_during_turn.mouth}; hands ${P.hidden_during_turn.hands}; hair ${P.hidden_during_turn.hair}. ${P.no_hold_note}`;
  qaStrip();
}
let lastTxt = '';
function ui() {
  const f = Math.round(wrapF(st.pos)), fr = FR[f - 1];
  const txt = `frame f${String(f).padStart(3, '0')}  ${fr.angle.toFixed(1)}°  phase ${st.phase}${st.target ? '  target f' + String(st.target).padStart(3, '0') : ''}\n` +
    (last && last.w > 0.001 ? `live parts (${last.view}) ${(last.w * 100).toFixed(0)}% · frame ${(100 - last.w * 100).toFixed(0)}%` : 'authored turn frame only · live parts hidden') + (Math.abs(st.swayX) > .05 ? `  sway ${st.swayX.toFixed(1)}px` : '');
  if (txt !== lastTxt) { $('#hud').textContent = txt; lastTxt = txt; }
  if (st.phase !== 'manual') $('#dial').value = f;
  $('#ph').style.left = ((f - 1) / (LOOP - 1) * 100) + '%';
  document.querySelectorAll('#phases span[data-p]').forEach(s => s.classList.toggle('on', s.dataset.p === st.phase));
}

/* ---------- angle_map polling: per-handoff scale/offset replaces the provisional fit when Body posts it ---------- */
function applyAngleMap(am) {
  let hs = am.handoffs || am.rest || am.fits;
  if (am.handoff && typeof am.handoff === 'object') hs = Object.entries(am.handoff).filter(([k, v]) => v && typeof v === 'object' && 'frame' in v).map(([k, v]) => ({ frame: v.frame, scale: v.scale, dx: v.dx, dy: v.dy }));
  if (!Array.isArray(hs)) return false;
  const fit = {}; for (const h of hs) { const f = +String(h.frame ?? h.f).replace('f', ''); const off = h.offset || [h.dx ?? h.offsetX, h.dy ?? h.offsetY];
    if (f && Number.isFinite(+h.scale) && Number.isFinite(+off[0])) fit[f] = { scale: +h.scale, dx: +off[0], dy: +off[1] }; }
  const ks = Object.keys(fit).map(Number).sort((a, b) => a - b); if (ks.length < 2) return false;
  if (!fit[LOOP + 1] && fit[1]) { fit[LOOP + 1] = fit[1]; ks.push(LOOP + 1); }
  for (const fr of FR) { const i = Math.max(...ks.filter(k => k <= fr.f)), j = Math.min(...ks.filter(k => k >= fr.f).concat([ks[ks.length - 1]])); const w = i === j ? 0 : (fr.f - i) / (j - i);
    for (const k of ['scale', 'dx', 'dy']) fr[k] = fit[i][k] * (1 - w) + fit[j][k] * w; }
  const src = 'angle_map.json handoff scale/offset (polled live)'; const changed = P.fit_source !== src; P.fit_source = src; return changed;
}
async function pollAngleMap() { try { const r = await fetch('../../body_tools/work/apose_turn/angle_map.json', { cache: 'no-store' }); if (r.ok && applyAngleMap(await r.json())) buildRulesOnly(); } catch (e) {} setTimeout(pollAngleMap, 30000); }
function buildRulesOnly() { const el = $('#rules'); if (el) el.innerHTML = el.innerHTML.replace(/<b>Fit:<\/b>[^.]*\./, `<b>Fit:</b> ${P.fit_source}.`); }

/* ---------- test hooks ---------- */
window.SVDriver = {
  get state() { return { phase: st.phase, frame: Math.round(wrapF(st.pos)), angle: FR ? FR[Math.round(wrapF(st.pos)) - 1].angle : 0, target: st.target, auto: st.auto, w: st.w, view: st.handoffView, history: st.history.slice(), talk: st.talk, flashSkips: st.flashSkips, handoffs: st.handoffs, last, opt: { ...opt } }; },
  goTo: f => goTo(f), setAuto: v => { st.auto = v; $('#play').classList.toggle('on', v); }, scrubTo, setOpt: o => Object.assign(opt, o),
  startTalk, stopTalk, drawNow: () => draw(), video: tv, rigReady: () => Object.fromEntries(Object.entries(RIG).map(([k, v]) => [k, v.ready])), ready: false,
  setW: (w, view) => { if (view) { st.handoffView = view; } st.w = st.wFrom = st.wTo = w; },   // QA only: freeze the handoff crossfade weight
  preload: async (a, b) => { for (let f = a; f <= b; f++) await keyed(f); }
};
fetch('poses.json', { cache: 'no-store' }).then(r => r.json()).then(async j => {
  P = j; FR = j.frames; LOOP = j.loop_end || 232; opt.base = P.handoffs[0].frame; st.pos = opt.base; buildUI();
  for (const h of P.handoffs) rigFrame(h.view);
  await keyed(opt.base);
  const t0 = performance.now(); while (!(RIG[P.handoffs[0].view] && RIG[P.handoffs[0].view].ready) && performance.now() - t0 < 20000) await new Promise(r => setTimeout(r, 200));
  st.handoffView = P.handoffs[0].view; st.w = 1; st.wFrom = st.wTo = 1;
  setPhase('idle', performance.now()); window.SVDriver.ready = true; requestAnimationFrame(loop);
  pollAngleMap();
  (async () => { for (let f = 1; f <= LOOP; f++) { try { await loadImg(FR[f - 1].src); } catch (e) {} } })();   // warm the image cache in order
});
