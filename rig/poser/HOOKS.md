# Hooks for rig/poser.html (proposed patches to rig/index.html, not applied)

`rig/poser.html` works **today without any change** to `rig/index.html`. It reaches into the same-origin iframe through the rig's script globals,
the same way `app/rigctl.js` and `app/driver/simple.html` already do:
- `P`, `v`, `inputs`, `set(k,x)`, `draw()` and `RigManual()`
- `mouthPick()`, `makeAnim(seed)`, `stepHair(A,dt)`, `hairDrive` (assigned through `eval`), `coeff(b,k)`, `bodyParamOf(b)` and `restPixels()`
- `R.skin.bones`, `R.feet`, `R.eyes.irisLimitsPx`, `R.mouthShapes`, `R.hairInfo` and `RigTwist.maxDegrees`
- the `#rest`, `#hairpreset`, `#mouthfade`, `#bodymode` and `#underlay` elements

The poser also injects one `<style>` into the iframe to hide the rig's own panels.

That works, but it depends on internals another worker is editing. Each patch below is additive. With no caller, behaviour is byte-identical (rest stays 0 px, and the live default is unchanged).
In priority order:

## H1. `window.RigAPI`: a stable, eval-free surface (replaces all the lexical-global reads)
Insert right after the `window.RigPartMesh=...` line (currently line ~465), or anywhere after `draw` and `mouthPick` are defined:
```js
window.RigAPI={version:1,
 get ready(){return !!R&&!R.loading}, get view(){return view}, params(){return JSON.parse(JSON.stringify(P))},
 enabled(k){return !!inputs[k]&&!inputs[k].disabled}, values(){return {...v}},
 setValues(o,{redraw=true}={}){for(const k in o)if(k in P&&inputs[k]&&!inputs[k].disabled)set(k,clamp(+o[k],P[k][0],P[k][1]));if(redraw)draw()},
 reset(){document.getElementById('rest').click()},
 mouthShape(o,f){const a=v.MouthOpen,b=v.MouthForm;if(o!=null){v.MouthOpen=o;v.MouthForm=f}const r=mouthPick();v.MouthOpen=a;v.MouthForm=b;return r},
 mouthShapes(){return (R.mouthShapes||[]).map(s=>({id:s.id,name:s.name,open:s.open,form:s.form}))},
 jointDeg(k){const bs=R.skin?R.skin.bones:(R.body?R.body.parts:[]);const b=bs.find(p=>bodyParamOf(p)===k);return b?coeff(b,k):null},
 bones(){const bs=R.skin?R.skin.bones:(R.body?R.body.parts:[]);return bs.map(b=>({id:b.id,parent:b.parent??null,pivot:[b.pivotX,b.pivotY],param:bodyParamOf(b)}))},
 feet(){return R.feet?JSON.parse(JSON.stringify({L:R.feet.L&&{pts:R.feet.L.pts.map(p=>({x:p.x,y:p.y}))},R:R.feet.R&&{pts:R.feet.R.pts.map(p=>({x:p.x,y:p.y}))},line:R.feet.line})):null},
 irisLimits(){return R.eyes&&R.eyes.irisLimitsPx||null}, noFace(){return !!R.noFace},
 renderTo(canvas){const g=guard(canvas.getContext('2d'));render(g,Object.keys(P).every(k=>v[k]===P[k][2])&&!hairDrive)}};
document.dispatchEvent(new CustomEvent('rig-ready'));   // also dispatch at the end of load() once R.loading is false
```
Also dispatch `rig-ready` at the end of `load()`, after `R.loading=false`. The poser would then stop polling `typeof R`.

## H2. Deterministic hair: snapshot and restore the spring state
Today the poser bakes hair by calling `stepHair(A,dt)` with its own `A=makeAnim(seed)` at a fixed step, then reading and assigning the global `hairDrive`
through `eval`. A stable form, added next to `stepHair`:
```js
window.RigHair={
 newState(seed){return makeAnim(seed|0)},                                     // fresh spring state (all strands at rest)
 step(A,dt){stepHair(A,dt);return JSON.parse(JSON.stringify(hairDrive||{}))}, // advance one fixed step, return the per-strand drive
 apply(drive){hairDrive=drive?JSON.parse(JSON.stringify(drive)):null;if(!drive){set('HairSwayX',0);set('HairSwayY',0)}},
 setPreset(p){const e=document.getElementById('hairpreset');if(e&&[...e.options].some(o=>o.value===p)){e.value=p;HAIR_PRESET=p}}};
```

## H3. Mouth crossfade clock
The 35 ms mouth crossfade runs on `performance.now()`. A scrubbed frame and a played frame could therefore differ, so the poser forces `#mouthfade` to 0 (hard cut) whenever the timeline has keys.
Proposed: `window.RigClock={set(ms){simNow=ms},clear(){simNow=null}}`. `simNow` already exists for the motion-quality path. The fade can then be evaluated at timeline time, and the poser can keep the 35 ms fade during playback.

## H4. `?embed=1`: hide the rig UI without style injection
In the `<style>` block: `body.embed #ui,body.embed #layers,body.embed #pose-toolbar,body.embed #pose-nodes{display:none!important}`.
At startup: `if(new URLSearchParams(location.search).get('embed')==='1')document.body.classList.add('embed')`.

## H5. postMessage bridge (only if the poser must ever run cross-origin, e.g. a tunnel URL on another host)
```js
addEventListener('message',e=>{if(e.origin!==location.origin)return;const m=e.data||{};if(m.type==='rig:set'){RigAPI.setValues(m.values||{})}
 else if(m.type==='rig:reset')RigAPI.reset();else if(m.type==='rig:get')e.source.postMessage({type:'rig:values',values:RigAPI.values(),id:m.id},e.origin)});
```

Not needed: setting controls through the URL. The poser saves and loads pose JSON itself.
