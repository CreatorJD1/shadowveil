# v1.8 part 5: edge seal. Abutting antialiased cut edges composited with source-over leave net partial alpha (a+b-ab < 1) inside the
# character. Posed frames also accumulate a coverage buffer (every item drawn again with 'lighter', i.e. summed premultiplied alpha,
# clamped at 1) and raise the composite's alpha to that coverage where it is higher. Colour stays the composite's own
# (un-premultiplied) mix. Drawn with drawImage + composite operations only (the dev guard forbids pixel writes). Single-layer edges (the outer silhouette) are unchanged; rest is never touched.
import sys
src,dst=sys.argv[1],sys.argv[2]
s=open(src).read()
def R(old,new,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'patch anchor found {n}x (want {count}): {old[:90]!r}')
    s=s.replace(old,new)
R('<label><span>Auto style (v1.8)</span>',
  '<label><span>Edge seal (v1.8)</span><select id="seal"><option value="1">on: seal abutting part edges</option><option value="0">off</option></select></label>\n<label><span>Auto style (v1.8)</span>')
R("['quality','quality']]){","['quality','quality'],['seal','seal']]){")
old=" try{for(let i=0;i<list.length;){DIM=LPA?LP.dim(list[i].m):1;if(list[i].skin){let j=i;const grs=[];while(j<list.length&&list[j].skin&&(LPA?LP.dim(list[j].m):1)===DIM){grs.push(list[j].skin);j++}skinPass(g,grs,list[i].pose);i=j}else{list[i].fn(g);i++}}}finally{DIM=1}}"
new=(" const pass=q=>{for(let i=0;i<list.length;){DIM=LPA?LP.dim(list[i].m):1;if(list[i].skin){let j=i;const grs=[];while(j<list.length&&list[j].skin&&(LPA?LP.dim(list[j].m):1)===DIM){grs.push(list[j].skin);j++}skinPass(q,grs,list[i].pose);i=j}else{list[i].fn(q);i++}}};\n"
     " try{pass(g);if(!rest&&!LPA&&sealOn())sealEdges(g,pass)}finally{DIM=1}}\n"
     "let COV=null;function sealOn(){const e=document.getElementById('seal');return !e||e.value!=='0'}\n"
     "function sealEdges(g,pass){const cw=g.canvas.width,ch=g.canvas.height;const mk=()=>{const c=document.createElement('canvas');c.width=cw;c.height=ch;return c};\n"
     " if(!COV||COV.width!==cw||COV.height!==ch){COV=mk();SEALC=mk()}\n"
     " // coverage C: every item again, summed with 'lighter' (alpha = min(1, sum of premultiplied alphas))\n"
     " const q=guard(COV.getContext('2d'));q.__S=g.__S;q.setTransform(1,0,0,1,0,0);q.globalAlpha=1;q.globalCompositeOperation='source-over';q.clearRect(0,0,cw,ch);q.globalCompositeOperation='lighter';pass(q);q.globalCompositeOperation='source-over';\n"
     " // D: the composite over itself 8x (destination-over keeps its un-premultiplied colour, alpha -> 1), then D destination-in C\n"
     " const d=guard(SEALC.getContext('2d'));d.setTransform(1,0,0,1,0,0);d.globalAlpha=1;d.imageSmoothingEnabled=false;d.globalCompositeOperation='source-over';d.clearRect(0,0,cw,ch);d.drawImage(g.canvas,0,0);\n"
     " d.globalCompositeOperation='destination-over';for(let k=0;k<8;k++)d.drawImage(SEALC,0,0);d.globalCompositeOperation='destination-in';d.drawImage(COV,0,0);d.globalCompositeOperation='source-over';\n"
     " g.save();g.setTransform(1,0,0,1,0,0);g.globalAlpha=1;g.globalCompositeOperation='source-over';g.imageSmoothingEnabled=false;g.clearRect(0,0,cw,ch);g.drawImage(SEALC,0,0);g.restore()}\n"
     "let SEALC=null;")
R(old,new)
open(dst,'w').write(s);print('ok',len(s))
