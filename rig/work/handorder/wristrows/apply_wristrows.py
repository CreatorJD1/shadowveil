#!/usr/bin/env python3
"""Idempotent ?handorder=1 wrist-row fix for rig/index.html (left/right only, staged flag).
On the 1-2 wrist rows where Body's forearm (layer 250) covers the palm, the palm is drawn again just above the forearm,
clipped to hands/<view>_hand_erase_mask.png ∩ those rows (rest-space clip, moves with the palm's own transform).
usage: apply_wristrows.py IN OUT"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
if 'HO_WRIST_ROWS' in s:
    open(dst, 'w').write(s); print('already patched'); sys.exit(0)
R = []
a0 = "function hairlessOrder(Z,vw){"
R.append((a0, r"""// ?handorder=1 wrist rows (staged): rows from rig/work/handorder/ho_pts.json (left 53 px y852-853, right 24 px y856-857)
const HO_WRIST_ROWS={left:{L_palm:[852,853]},right:{R_palm:[856,857]}};
async function hoWristSetup(r,vw){const rows=HO_WRIST_ROWS[vw];if(!rows)return null;const mk=await img('../hands/'+vw+'_hand_erase_mask.png');if(!mk){r.warn.push('handorder wrist rows: hands/'+vw+'_hand_erase_mask.png not loaded');return null}
 const mc=document.createElement('canvas');mc.width=W;mc.height=H;const mq=mc.getContext('2d');mq.drawImage(mk,0,0);const M=mq.getImageData(0,0,W,H).data;const out={};
 for(const id in rows){const pi=r.im['hands:'+id];if(!pi||pi.empty)continue;const c=document.createElement('canvas');c.width=W;c.height=H;const q=c.getContext('2d');q.drawImage(pi,pi.ox||0,pi.oy||0);const d=q.getImageData(0,0,W,H);const D=d.data;let n=0;
  for(let y=0;y<H;y++){const on=rows[id].includes(y);for(let x=0;x<W;x++){const i=(y*W+x)*4;if(!on||!(M[i]>127||M[i+3]>127&&M[i]+M[i+1]+M[i+2]>381)){D[i+3]=0}else if(D[i+3])n++}}
  q.putImageData(d,0,0);const t=trim(c);t.hoPx=n;out[id]=t;r.warn.push('staged handorder: '+id+' wrist rows '+rows[id].join('-')+' drawn over forearm ('+n+' px, erase mask ∩ rows)')}
 return out}
""" + a0))
a1 = "r.loading=false;R=r;LP.key='';"
R.append((a1, "if(HANDORDER&&HO_WRIST_ROWS[view]){r.hoWrist=await hoWristSetup(r,view);if(generation!==loadGeneration)return}" + a1))
a2 = "g=>{drawM(g,need('hands:'+p.id,f?f.img:im['hands:'+p.id]),M[p.id])},{id:'hands:'+p.id,gid:'hands:'+H0,glabel:(H0==='L'?'left':'right')+' hand ('+H0+')',sys:'hands',label:p.id,info,ginfo})"
R.append((a2, a2 + ";if(R.hoWrist&&R.hoWrist[p.id]&&!f&&!(R.pm&&R.pm['hands:'+p.id])){const zf=Z['body:forearm_'+H0];add(Number.isFinite(zf)?zf:250,STEP.hands,g=>{drawM(g,R.hoWrist[p.id],M[p.id])},{id:'hands:'+p.id+':wristrows',gid:'hands:'+H0,glabel:(H0==='L'?'left':'right')+' hand ('+H0+')',sys:'hands',label:p.id+' wrist rows (over forearm)',info:R.hoWrist[p.id].hoPx+' px'})}"))
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'anchor count {n}: {a[:70]}')
    s = s.replace(a, b)
open(dst, 'w').write(s); print('patched', len(R))
