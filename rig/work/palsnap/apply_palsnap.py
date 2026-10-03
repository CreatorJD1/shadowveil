#!/usr/bin/env python3
"""Idempotent ?palsnap=1 patch for rig/index.html (staged flag; default path unchanged).
usage: apply_palsnap.py IN OUT   -- applies only if the PALSNAP marker is absent; every anchor must match exactly once."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
if 'const PALSNAP=' in s:
    open(dst, 'w').write(s); print('already patched'); sys.exit(0)
R = []
R.append(("let QUAL='ss2';", "let QUAL='ss2';" + r"""
// ?palsnap=1 (staged): posed frames only. Every draw item is rasterised into its own layer with the normal filter, then each
// pixel that is not an exact RGBA texel of that item's own source art is snapped: alpha < palsnapa (default 128) -> 0, else alpha 255 and RGB -> the nearest tone of THAT item's own source art
// (images it drew: part PNG / finger frame / skin + underlay texture / eye layer of that eye). Tones never cross parts or eyes.
// ss2 downsample is skipped (it would re-mix tones); the mouth cross-fade becomes a hard switch at alpha 0.5. Rest frames are never touched.
const PALSNAP=new URLSearchParams(location.search).get('palsnap')==='1';const PS_A=+(new URLSearchParams(location.search).get('palsnapa')||128);
let PS_REC=null,PS_BB=null,PS_L=null;const PS_PAL=new WeakMap();const PS_STATS={frames:0,items:0,kept:0,snapped:0,dropped:0,ms:0};
function psPal(im){if(!im||im.empty)return null;let p=im.__psDyn?null:PS_PAL.get(im);if(p)return p;const w=im.naturalWidth||im.width,h=im.naturalHeight||im.height;if(!w||!h)return null;
 const c=document.createElement('canvas');c.width=w;c.height=h;const q=c.getContext('2d',{willReadFrequently:true});q.drawImage(im,0,0);const d=q.getImageData(0,0,w,h).data;const s=new Set(),x=new Set();
 for(let i=0;i<d.length;i+=4){const a=d[i+3];if(!a)continue;x.add(((d[i]<<24)|(d[i+1]<<16)|(d[i+2]<<8)|a)>>>0);if(a===255)s.add((d[i]<<16)|(d[i+1]<<8)|d[i+2])}if(!s.size)for(let i=0;i<d.length;i+=4)if(d[i+3]>0)s.add((d[i]<<16)|(d[i+1]<<8)|d[i+2]);
 p={rgb:Int32Array.from(s),rgba:x};if(!im.__psDyn)PS_PAL.set(im,p);return p}
function psBox(M,x,y,w,h,S){if(!PS_REC)return;const C=[[x,y],[x+w,y],[x,y+h],[x+w,y+h]].map(([a,b])=>[S*(M[0]*a+M[2]*b+M[4]),S*(M[1]*a+M[3]*b+M[5])]);const b=[Math.floor(Math.min(...C.map(p=>p[0])))-2,Math.floor(Math.min(...C.map(p=>p[1])))-2,Math.ceil(Math.max(...C.map(p=>p[0])))+2,Math.ceil(Math.max(...C.map(p=>p[1])))+2];
 PS_BB=PS_BB?[Math.min(PS_BB[0],b[0]),Math.min(PS_BB[1],b[1]),Math.max(PS_BB[2],b[2]),Math.max(PS_BB[3],b[3])]:b}
function psWrap(q,fn){if(!PALSNAP||!POSED){fn(q);return}const t0=performance.now();const cw=q.canvas.width,ch=q.canvas.height;if(!PS_L)PS_L=document.createElement('canvas');if(PS_L.width!==cw||PS_L.height!==ch){PS_L.width=cw;PS_L.height=ch}
 const L=PS_L.getContext('2d',{willReadFrequently:true});L.__S=q.__S;L.setTransform(1,0,0,1,0,0);L.globalAlpha=1;L.globalCompositeOperation='source-over';L.clearRect(0,0,cw,ch);
 const pr=PS_REC,pb=PS_BB;PS_REC=[];PS_BB=null;let rec,bb;try{fn(L)}finally{rec=PS_REC;bb=PS_BB;PS_REC=pr;PS_BB=pb}
 const set=new Set(),ex=[];for(const im of rec){const p=psPal(im);if(p){for(const c of p.rgb)set.add(c);ex.push(p.rgba)}}if(!set.size){const p=psPal(R.im.base);if(p){for(const c of p.rgb)set.add(c);ex.push(p.rgba)}}const pal=Int32Array.from(set);
 const exact=k=>{for(const e of ex)if(e.has(k))return true;return false};
 const x0=Math.max(0,bb?bb[0]:0),y0=Math.max(0,bb?bb[1]:0),x1=Math.min(cw,bb?bb[2]:cw),y1=Math.min(ch,bb?bb[3]:ch);
 if(x1>x0&&y1>y0&&pal.length){const img=L.getImageData(x0,y0,x1-x0,y1-y0),d=img.data,memo=new Map();
  for(let i=0;i<d.length;i+=4){const a=d[i+3];if(!a)continue;if(exact(((d[i]<<24)|(d[i+1]<<16)|(d[i+2]<<8)|a)>>>0)){PS_STATS.kept++;continue} // an exact texel of her art (rest, whole-px moves, nearest samples): untouched
   if(a<PS_A){d[i]=d[i+1]=d[i+2]=d[i+3]=0;PS_STATS.dropped++;continue}
   const k=(d[i]<<16)|(d[i+1]<<8)|d[i+2];let c=memo.get(k);if(c===undefined){let be=1e9;c=k;for(let j=0;j<pal.length;j++){const t=pal[j],er=(t>>16&255)-d[i],eg=(t>>8&255)-d[i+1],eb=(t&255)-d[i+2],e=er*er+eg*eg+eb*eb;if(e<be){be=e;c=t;if(!e)break}}memo.set(k,c)}
   d[i]=c>>16&255;d[i+1]=c>>8&255;d[i+2]=c&255;d[i+3]=255;PS_STATS.snapped++}
  L.putImageData(img,x0,y0)}
 q.save();q.setTransform(1,0,0,1,0,0);q.globalAlpha=1;q.imageSmoothingEnabled=false;if(x1>x0&&y1>y0)q.drawImage(PS_L,x0,y0,x1-x0,y1-y0,x0,y0,x1-x0,y1-y0);q.restore();PS_STATS.items++;PS_STATS.ms+=performance.now()-t0}
window.RigPalSnap={get on(){return PALSNAP},get alpha(){return PS_A},stats(){return{...PS_STATS}},reset(){for(const k in PS_STATS)PS_STATS[k]=0}};"""))
# drawM: record source + bbox (no-op when PS_REC is null, i.e. always unless palsnap is wrapping an item)
R.append(("function drawM(g,im,M,alpha){if(!im||im.empty)return;g.save();const ox=im.ox||0,oy=im.oy||0,S=g.__S||1;",
          "function drawM(g,im,M,alpha){if(!im||im.empty)return;g.save();const ox=im.ox||0,oy=im.oy||0,S=g.__S||1;if(PS_REC){PS_REC.push(im);psBox(M,ox,oy,im.width,im.height,S)}"))
# GL mesh passes: record texture source, full-canvas bbox
R.append(("function meshDraw(Mh,ranges,filt,S){const gl=SKGL.gl,cv=SKGL.cv;",
          "function meshDraw(Mh,ranges,filt,S){const gl=SKGL.gl,cv=SKGL.cv;if(PS_REC){const t=Mh.img||Mh.texFor;if(t)PS_REC.push(t);PS_BB=[0,0,W*S,H*S]}"))
R.append(("mesh.tex=glTex(gl,canvas);", "mesh.tex=glTex(gl,canvas);mesh.img=canvas;"))
# donor hand raster: bbox from its raster rect (sources recorded by the inner drawM / meshDraw calls)
R.append(("g.save();g.setTransform(S,0,0,S,S*x,S*y);g.imageSmoothingEnabled=false;g.globalAlpha=DIM;g.drawImage(c,0,0,w,h);g.restore()}",
          "if(PS_REC){psBox([1,0,0,1,0,0],x,y,w,h,S);if(!PS_REC.length)PS_REC.push(im)}g.save();g.setTransform(S,0,0,S,S*x,S*y);g.imageSmoothingEnabled=false;g.globalAlpha=DIM;g.drawImage(c,0,0,w,h);g.restore()}"))
# eye layer canvases are rebuilt every frame: never cache their palette
R.append(("o=eyeCanvas[E]=document.createElement('canvas');", "o=eyeCanvas[E]=document.createElement('canvas');o.__psDyn=1;"))
# ss2: snapped frames render at 1x (a 2x downsample would re-blend tones)
R.append(("function renderFinal(g,rest){if(rest||QUAL!=='ss2'||", "function renderFinal(g,rest){if(rest||QUAL!=='ss2'||(PALSNAP&&!rest)||"))
# item pass: wrap each item / skin group
R.append(("skinPass(q,grs,list[i].pose);i=j}else{list[i].fn(q);i++}}};",
          "const pz=list[i].pose;psWrap(q,L=>skinPass(L,grs,pz));i=j}else{const it=list[i];psWrap(q,L=>it.fn(L));i++}}};if(PALSNAP&&!rest)PS_STATS.frames++;"))
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor count {n}: {a[:70]}')
    s = s.replace(a, b)
open(dst, 'w').write(s); print('patched', len(R), 'anchors')
