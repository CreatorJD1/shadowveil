#!/usr/bin/env python3
"""Apply the ?diag=1 patch to an index.html (re-runnable on the CURRENT file so other workers' edits are merged, never clobbered).
usage: patch_index.py <in.html> <out.html>. Every anchor must match exactly once, else it aborts."""
import sys
src = open(sys.argv[1]).read(); s = src
if 'DIAG SLOTS (staged' in s: sys.exit('already patched')
def rep(old, new):
    global s
    n = s.count(old)
    if n != 1: sys.exit(f'anchor count {n}: {old[:80]}')
    s = s.replace(old, new)
BLOCK = r"""
// DIAG SLOTS (staged, ?diag=1; off by default; views/ and rig.json untouched): the 4 diagonal turn angles as posable slots,
// rig/work/diag_rig/slots/d045|d135|d225|d315/ = her turn frame f033/f087/f131/f191 in FRAME px at (0,0) on the rig canvas
// (no resampling, no mirroring), shared skeleton + controls. diag.json per slot: crop, viewFit (display note), locks.
// ?diagmouth=1 (sub-flag, off): mouth/rig_diagmouth.json open shapes if delivered (none yet). Rest only otherwise.
const DIAG=new URLSearchParams(location.search).get('diag')==='1';const DIAGMOUTH=DIAG&&new URLSearchParams(location.search).get('diagmouth')==='1';
const DIAGWRIST=DIAG&&new URLSearchParams(location.search).get('diagwrist')==='1'; // test toggle (Hands): unlock wrist bend in the diag slots
const DIAGBEND=DIAG&&new URLSearchParams(location.search).get('diagbend')==='1'; // prototype toggle: unlock body joints (rejected pieces, or the mesh with &skin=skin.json)
const DIAG_VIEWS=new Set(['d045','d135','d225','d315']);const DIAG_NOFACE=new Set(['d135','d225']);
function isDiag(vw){return DIAG&&DIAG_VIEWS.has(vw)}
function viewBase(vw){return isDiag(vw)?'work/diag_rig/slots/'+vw+'/':'../views/'+vw+'/'}
if(DIAG){const s=document.getElementById('view');for(const d of DIAG_VIEWS){const o=document.createElement('option');o.value=d;o.textContent=d+' (diag)';s.append(o)}}
function diagLock(){if(!R||!R.diag||!R.diag.locks)return;const G=R.diag.lockGroups||{},skip=new Set([...(DIAGBEND?G.body||[]:[]),...(DIAGWRIST?G.wrist||[]:[])]);for(const k in R.diag.locks)if(k in v&&!skip.has(k)){v[k]=R.diag.locks[k];if(inputs[k]){inputs[k].value=v[k];inputs[k].disabled=true;inputs[k].parentNode.style.opacity=.4;inputs[k].parentNode.title='locked in this diagonal slot: '+(R.diag.locksWhy||'')}}}
// per-eye iris limits (Coder irislimits v4): oval clamp, X/Y extremes per eye, whole-px corner caps when looking up/down and sideways
function diagIris(E,X,Y,dx,dy){const j=R&&R.eyes,L=DIAG&&j&&j.irisLimitsPxPerEye&&j.irisLimitsPxPerEye[E];if(!L)return[dx,dy];let gx=X,gy=Y;const r=Math.hypot(gx,gy);if(r>1){gx/=r;gy/=r}
 let ex=Math.round(gx*(gx>0?L.dxAtXplus1:-L.dxAtXminus1)),ey=Math.round(gy*(gy>0?L.dyAtYplus1:-L.dyAtYminus1));if(ey&&ex&&L.corners){const c=L.corners[(gx>0?'+1':'-1')+','+(gy>0?'+1':'-1')];if(c)ex=Math.sign(ex)*Math.min(Math.abs(ex),Math.abs(c[0]))}return[ex+0,ey+0]}
// per-part hair sway cap (Hair v4 contract: part.swayCap {min,max} in [-1,1]); only read in diag slots
function diagSway(p,x){const c=DIAG&&p&&p.swayCap;if(!c)return x;return clamp(x,c.min!=null?+c.min:-1,c.max!=null?+c.max:1)}
"""
rep("const W=1365,H=1739;\n", "const W=1365,H=1739;\n" + BLOCK.lstrip('\n'))
rep("function hairlessOrder(Z,vw){", "function hairlessOrder(Z,vw){if(isDiag(vw)){for(const k in Z)if(k.startsWith('hands:')&&Z[k]>=300&&Z[k]<=399)Z[k]=210+(Z[k]-300)*0.25;return} // diag: hands under the forearms (Hands F8)\n")
rep("async function loadHandAngles(r,vw,hands){", "async function loadHandAngles(r,vw,hands){if(isDiag(vw))return{}; // diag slots: authored F8/F12 hands only, no generated turned hands\n")
rep("const b='../views/'+view+'/';", "const b=viewBase(view);")
rep("const noFace=NO_FACE_VIEWS.has(view);", "const noFace=NO_FACE_VIEWS.has(view)||(isDiag(view)&&DIAG_NOFACE.has(view));")
rep("(noFace&&(s==='eyes'||s==='mouth'))?null:json(b+s+'/rig.json')", "(noFace&&(s==='eyes'||s==='mouth'))?null:(s==='mouth'&&isDiag(view)&&DIAGMOUTH)?json(b+'mouth/rig_diagmouth.json').then(x=>x||json(b+'mouth/rig.json')):json(b+s+'/rig.json')")
rep("r.loading=false;R=r;LP.key='';", "r.diag=isDiag(view)?await json(b+'diag.json'):null;if(generation!==loadGeneration)return;r.loading=false;R=r;diagLock();LP.key='';")
rep("function draw(){if(!R||R.loading)return;", "function draw(){if(!R||R.loading)return;if(R.diag)diagLock();")
rep("let z=Z[document.getElementById('zoom').value];", "let z=Z[document.getElementById('zoom').value];if(R.diag&&R.diag.crop){const zv=document.getElementById('zoom').value,F=R.diag.viewFit||{scale:1,dx:0,dy:0};if(zv==='full')z=R.diag.crop;else if(zv==='head')z=[(Z.head[0]-F.dx)/F.scale,(Z.head[1]-F.dy)/F.scale,Z.head[2]/F.scale,Z.head[3]/F.scale]}")
rep("q.drawImage(ir,dx+(ir.ox||0),dy+(ir.oy||0))", "{const[ex,ey]=diagIris(E,X,Y,dx,dy);q.drawImage(ir,ex+(ir.ox||0),ey+(ir.oy||0))}")
rep("const a=(p.swayWeight||0)*(p.maxSwayDeg||0)*clamp(d?d.x:v.HairSwayX,-1,1)", "const a=(p.swayWeight||0)*(p.maxSwayDeg||0)*diagSway(p,clamp(d?d.x:v.HairSwayX,-1,1))")
open(sys.argv[2], 'w').write(s); print('patched', len(src), '->', len(s))
