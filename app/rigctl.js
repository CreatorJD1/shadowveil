/* Shadowveil master app: "Rig controls" panel for #body.
   Embeds the rig (v1.8 WIP, falls back to rig/index.html) in a same-origin iframe and drives it
   ONLY by setting the rig's own parameters: the rig's global set(k,x) + draw(), i.e. exactly what its
   own sliders do (slider moves in either panel stay in sync). It never draws on the character.
   Controllers are auto-detected from the rig's param table P at every load, so params the rig worker
   adds later (WristRot*, *Twist*, split-curl/claw) switch from "in progress" to live by themselves.
   Views: the dial/arrows reload the iframe with ?view=<authored view> (no mirroring). */
'use strict';
window.RigCtl = (() => {
  const SRC = ['rig/index.v18-wip.html', 'rig/index.html'];
  const FINGERS = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'];
  const DIAL = { apose: 0, right: 90, back: 180, left: 270 };      // tpose sits in the dial centre (front, arms out)
  // expected-but-not-yet-built controllers (shown disabled until P has a matching key)
  const PENDING = {
    wrist: [['WristRotL', /^WristRot(ate)?L$/], ['WristRotR', /^WristRot(ate)?R$/], ['PalmTwistL', /^PalmTwistL$/], ['PalmTwistR', /^PalmTwistR$/]],
    twist: [['ShoulderTwistL/R', /^(Shoulder|UpperArm)Twist[LR]$/], ['ForearmTwistL/R', /^(Forearm|Elbow)Twist[LR]$/], ['WristTwistL/R', /^WristTwist[LR]$/],
            ['HipTwistL/R', /^(Hip|Thigh)Twist[LR]$/], ['KneeTwistL/R', /^(Knee|Shin)Twist[LR]$/], ['AnkleTwistL/R', /^(Ankle|Foot)Twist[LR]$/], ['NeckTwist', /^(Neck|Head)Twist$/]],
    split: [['Per-joint curl L (Index1..3 …)', /^HandL(Thumb|Index|Middle|Ring|Pinky)[123]$/], ['Per-joint curl R', /^HandR(Thumb|Index|Middle|Ring|Pinky)[123]$/],
            ['Claw L', /^(HandL(Claw|Split)|ClawL)/], ['Claw R', /^(HandR(Claw|Split)|ClawR)/]],
  };
  let st = null;                       // {wrap, fr, cw, src, view, keys, vals, els}
  const saved = { view: 'apose', vals: {} };
  const $h = (t, a = {}, ...c) => { const e = document.createElement(t); for (const [k, v] of Object.entries(a)) { if (k === 'on') for (const [ev, f] of Object.entries(v)) e.addEventListener(ev, f); else if (v !== false && v != null) e.setAttribute(k, v === true ? '' : v) } for (const x of c.flat()) if (x != null) e.append(x.nodeType ? x : document.createTextNode(x)); return e };
  const css = `.rc{display:grid;grid-template-columns:1fr 300px;height:100%}.rc .rf{position:relative;overflow:hidden;background:#2a2a30}.rc .rf iframe{position:absolute;left:0;top:0;border:0;transform-origin:0 0}
  .rc .rp{overflow:auto;border-left:1px solid var(--line);padding:6px 8px;font-size:12px;background:var(--panel)}
  .rc h4{margin:8px 0 3px;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--dim);display:flex;gap:6px;align-items:center}
  .rc .row{display:grid;grid-template-columns:78px 1fr 34px;gap:4px;align-items:center;padding:1px 0}.rc .row input{width:100%}.rc .row .val{color:var(--dim);font-size:10px;text-align:right}
  .rc .row.off{opacity:.45}.rc .ip{font-size:9px;background:#3d2f12;color:#f1c56a;border-radius:3px;padding:0 4px;white-space:nowrap}
  .rc .live{font-size:9px;background:#1d3a28;color:#7fe0a0;border-radius:3px;padding:0 4px}
  .rc .dial{display:flex;align-items:center;gap:6px;justify-content:center}.rc .dial svg{width:132px;height:132px}
  .rc .dial svg text{font:10px system-ui;fill:#cfd5df;cursor:pointer;text-anchor:middle;dominant-baseline:middle}.rc .dial svg .on{fill:#fff;font-weight:700}
  .rc-wide{grid-template-columns:1fr!important}.rc-wide>#botside{display:none}
  .rc .btns{display:flex;gap:4px;flex-wrap:wrap}.rc .msg{color:var(--dim);font-size:11px;margin:4px 0}`;
  function ensureCss() { if (!document.getElementById('rigctl-css')) document.head.append($h('style', { id: 'rigctl-css' }, css)) }

  function fit(wrap, fr, minw) {
    const f = () => { const w = wrap.clientWidth, h = wrap.clientHeight; if (!w || !h) return; const s = Math.min(1, w / minw); fr.style.width = (w / s) + 'px'; fr.style.height = (h / s) + 'px'; fr.style.transform = s < 1 ? `scale(${s})` : '' };
    if (st?.ro) st.ro.disconnect(); const ro = new ResizeObserver(f); ro.observe(wrap); f(); return ro;
  }
  const ev = (cw, js) => cw.eval(js);  // same-origin: read the rig's lexical globals (P, v, inputs)

  function mount(host, note) {
    ensureCss();
    const box = $h('div', { class: 'rc' }), rf = $h('div', { class: 'rf' }), rp = $h('div', { class: 'rp', id: 'rigctl' }, $h('div', { class: 'msg' }, 'loading rig…'));
    box.append(rf, rp); host.replaceChildren(box);
    st = { wrap: rf, panel: rp, note, srcIdx: 0, view: saved.view };
    document.querySelector('#r-bot .cols')?.classList.add('rc-wide');
    load();
  }
  function unmount() { if (st?.ro) st.ro.disconnect(); if (st?.poll) clearInterval(st.poll); st = null; document.querySelector('#r-bot .cols')?.classList.remove('rc-wide') }

  function load() {
    const src = SRC[st.srcIdx], url = '../' + src + '?view=' + encodeURIComponent(st.view);
    const fr = $h('iframe', { src: url, title: 'rig ' + src }); st.wrap.replaceChildren(fr); st.fr = fr; st.src = src;
    st.ro = fit(st.wrap, fr, 1200);
    const my = st;
    fr.addEventListener('load', () => {
      if (st !== my) return;
      const cw = fr.contentWindow; let ok = false;
      try { ok = ev(cw, 'typeof P==="object"&&typeof set==="function"&&typeof draw==="function"') } catch { ok = false }
      if (!ok && st.srcIdx + 1 < SRC.length) { st.srcIdx++; load(); return }
      if (!ok) { st.panel.replaceChildren($h('div', { class: 'msg' }, 'Rig did not expose P/set/draw; controls unavailable.')); return }
      st.cw = cw; waitReady();
    });
  }
  // the rig loads its parts asynchronously; wait until the view select + inputs exist, then build the panel
  function waitReady(n = 0) {
    const my = st; if (!my) return;
    let ready = false; try { ready = ev(my.cw, 'Object.keys(inputs).length>0') && my.cw.document.getElementById('view') } catch { }
    if (!ready && n < 60) { setTimeout(() => st === my && waitReady(n + 1), 100); return }
    build();
    my.cw.document.addEventListener('input', sync, true); my.cw.document.addEventListener('click', () => setTimeout(sync, 30), true);
    waitParts();
  }
  // the rig's part images / skin mesh (R) can take many seconds; params only render once R exists
  function waitParts(n = 0) {
    const my = st; if (!my) return; let ok = false; try { ok = ev(my.cw, 'typeof R!=="undefined"&&!!R') } catch { }
    const ban = my.panel.querySelector('#rc-loading');
    if (!ok) { if (ban) ban.textContent = `rig parts loading… ${Math.round(n / 4)} s (sliders apply once loaded)`; if (n < 720) setTimeout(() => st === my && waitParts(n + 1), 250); return }
    for (const [k, x] of Object.entries(saved.vals)) setParam(k, x, false);   // restore values from before a view reload
    try { my.cw.draw() } catch { }
    my.ready = true; if (ban) ban.remove(); sync(); if (window.__rigctl) window.__rigctl.ready = true;
  }
  function P() { return ev(st.cw, 'P') }
  function vals() { return ev(st.cw, 'v') }
  function setParam(k, x, redraw = true) {
    const cw = st.cw; const P_ = P(); if (!(k in P_)) return;
    x = Math.min(P_[k][1], Math.max(P_[k][0], +x));
    try { cw.set(k, x) } catch { ev(cw, 'v')[k] = x }        // set() also moves the rig's own slider
    if (x === P_[k][2]) delete saved.vals[k]; else saved.vals[k] = x;
    if (redraw) cw.draw();
  }
  function sync() {
    if (!st?.els) return; const v = vals(); const inputs = ev(st.cw, 'inputs');
    for (const [k, e] of Object.entries(st.els)) { if (!(k in v)) continue; e.i.value = v[k]; e.o.textContent = (+v[k]).toFixed(2); const dis = inputs[k]?.disabled; e.i.disabled = !!dis; e.r.classList.toggle('off', !!dis); e.r.title = dis ? 'not driven in this view (rig has no body part for it)' : k }
    const hp = st.cw.document.getElementById('hairpreset'), mine = st.panel.querySelector('#rc-hair'); if (hp && mine) mine.value = hp.value;
  }

  function row(k, P_, label) {
    const [lo, hi, d] = P_[k]; const v = vals();
    const i = $h('input', { type: 'range', min: lo, max: hi, step: (hi - lo) > 4 ? 1 : 0.01, value: v[k], 'data-k': k });
    const o = $h('span', { class: 'val' }, (+v[k]).toFixed(2));
    const r = $h('div', { class: 'row' }, $h('span', { title: k }, label || k), i, o);
    i.addEventListener('input', () => { setParam(k, +i.value); o.textContent = (+i.value).toFixed(2) });
    i.addEventListener('dblclick', () => { setParam(k, d); sync() });
    st.els[k] = { i, o, r }; return r;
  }
  function pendingRow(label) { return $h('div', { class: 'row off pend', title: 'in progress: the rig does not have this parameter yet' }, $h('span', {}, label), $h('input', { type: 'range', disabled: true }), $h('span', { class: 'ip' }, 'in progress')) }
  function group(title, keys, P_, pend = [], lab = k => k) {
    const g = [$h('h4', {}, title, keys.length ? $h('span', { class: 'live' }, 'live') : null, !keys.length && pend.length ? $h('span', { class: 'ip' }, 'in progress') : null)];
    for (const k of keys) g.push(row(k, P_, lab(k)));
    for (const [label, re] of pend) if (!Object.keys(P_).some(k => re.test(k))) g.push(pendingRow(label));
    return g;
  }

  function build() {
    const P_ = P(), keys = Object.keys(P_), used = new Set(); st.els = {};
    const take = f => { const r = keys.filter(k => !used.has(k) && f(k)); r.forEach(k => used.add(k)); return r };
    const panel = st.panel; panel.replaceChildren($h('div', { class: 'msg', id: 'rc-loading', style: 'color:#f1c56a' }, 'rig parts loading…'));
    // view dial
    const views = [...st.cw.document.getElementById('view').options].map(o => o.value);
    const cur = st.view, step = d => { const i = views.indexOf(cur); goView(views[(i + d + views.length) % views.length]) };
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('viewBox', '-66 -66 132 132');
    svg.innerHTML = `<circle r="58" fill="#1c2029" stroke="#2a2f3b"/><circle r="20" fill="#232838" stroke="#2a2f3b"/>` +
      `<line x1="0" y1="0" x2="${(Math.sin((DIAL[cur] ?? 0) * Math.PI / 180) * 44).toFixed(1)}" y2="${(-Math.cos((DIAL[cur] ?? 0) * Math.PI / 180) * 44).toFixed(1)}" stroke="${cur === 'tpose' ? 'transparent' : '#58a6ff'}" stroke-width="3" stroke-linecap="round"/>`;
    for (const vw of views) {
      const a = DIAL[vw], t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      const [x, y] = a == null ? [0, 0] : [Math.sin(a * Math.PI / 180) * 44, -Math.cos(a * Math.PI / 180) * 44];
      t.setAttribute('x', x.toFixed(1)); t.setAttribute('y', y.toFixed(1)); t.textContent = vw; t.setAttribute('data-view', vw); if (vw === cur) t.setAttribute('class', 'on');
      t.addEventListener('click', () => goView(vw)); svg.append(t);
    }
    panel.append($h('h4', {}, 'View dial', $h('span', { class: 'live' }, 'live'), $h('span', { style: 'text-transform:none;letter-spacing:0' }, st.src.replace('rig/', ''))),
      $h('div', { class: 'dial' }, $h('button', { class: 'tab', id: 'rc-prev', title: 'previous authored view', on: { click: () => step(-1) } }, '◀'), svg,
        $h('button', { class: 'tab', id: 'rc-next', title: 'next authored view', on: { click: () => step(1) } }, '▶')),
      $h('div', { class: 'msg' }, `Authored views only, no mirroring. Changing view reloads the rig with ?view=. Now: ${cur}`),
      $h('div', { class: 'btns' }, $h('button', { class: 'tab', id: 'rc-reset', on: { click: reset } }, 'Reset to rest'),
        ...Object.entries({ Open: [0, 0, 0, 0, 0], Fist: [1, 1, 1, 1, 1], Point: [1, 0, 1, 1, 1], Peace: [1, 0, 0, 1, 1] }).map(([n, c]) => $h('button', { class: 'tab', on: { click: () => { for (const h of ['L', 'R']) FINGERS.forEach((f, i) => setParam('Hand' + h + f, c[i], false)); st.cw.draw(); sync() } } }, n))));
    // hands
    for (const h of ['L', 'R']) panel.append(...group(`Hand ${h}: finger curl`, take(k => new RegExp(`^Hand${h}(${FINGERS.join('|')}|Spread|ThumbSpread)$`).test(k)), P_, [], k => k.replace(/^Hand[LR]/, '')));
    panel.append(...group('Wrist rotation L / R', take(k => /^(Wrist(Rot(ate)?)?[LR]|PalmTwist[LR])$/.test(k)), P_, PENDING.wrist));
    panel.append(...group('Twist (arm / forearm / leg / neck)', take(k => /Twist/.test(k)), P_, PENDING.twist));
    panel.append(...group('Split finger curl (claw)', take(k => /^Hand[LR](Thumb|Index|Middle|Ring|Pinky)[123]$|Claw|Split/.test(k)), P_, PENDING.split, k => k.replace(/^Hand/, '')));
    panel.append(...group('Head', take(k => /^Head/.test(k)), P_));
    panel.append(...group('Body joints', take(k => /^(BodyLean|Shoulder|Elbow|Hip|Knee|Ankle|Toe)[LR]?$/.test(k)), P_));
    panel.append(...group('Root (px)', take(k => /^Root/.test(k)), P_));
    const hp = st.cw.document.getElementById('hairpreset');
    if (hp) { const s = $h('select', { id: 'rc-hair', on: { change: e => { hp.value = e.target.value; hp.dispatchEvent(new Event('change', { bubbles: true })) } } }, [...hp.options].map(o => $h('option', { value: o.value }, o.textContent)));
      s.value = hp.value; panel.append($h('h4', {}, 'Hair spring preset', $h('span', { class: 'live' }, 'live')), s) }
    const other = take(k => !/^(Eye|Mouth|HairSway)/.test(k));
    if (other.length) panel.append(...group('Other params (new in the rig)', other, P_));
    panel.append($h('div', { class: 'msg' }, 'Eyes, mouth and hair sway sliders stay in the rig\'s own panel (left). This panel only sets rig params via set()+draw(); double-click a slider to reset it.'));
    sync();
    const live = Object.keys(st.els).length, pend = panel.querySelectorAll('.row.pend').length;
    if (st.note) st.note.textContent = `Rig controls: ${live} live params from ${st.src} (auto-detected from P), ${pend} in progress. Views reload ?view=.`;
    window.__rigctl = { src: st.src, view: st.view, live: Object.keys(st.els), pending: [...panel.querySelectorAll('.row.pend span:first-child')].map(e => e.textContent), ready: !!st.ready };
  }
  function reset() { try { st.cw.document.getElementById('rest').click() } catch { const P_ = P(); for (const k in P_) setParam(k, P_[k][2], false); st.cw.draw() } saved.vals = {}; sync() }
  function goView(vw) { if (!st || vw === st.view) return; st.view = saved.view = vw; st.panel.replaceChildren($h('div', { class: 'msg' }, 'loading ' + vw + '…')); load() }
  return { mount, unmount, frame: () => st?.fr, state: () => st };
})();
