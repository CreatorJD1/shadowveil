#!/usr/bin/env python3
"""Eye targets for the six user benchmarks. Benchmarks are TARGETS ONLY (crop shown for comparison, never painted from).
Rig renders: views/apose via eyes/tools/render_eyes.py, diagonals via eyes/staged/diagonals/render_diag.py (Python compositing, no browser).
Writes sheet.png, targets.json, crops/ and rig/ tiles in this folder."""
import sys, json, os
sys.path.insert(0,'/workspace/shadowveil/eyes/tools'); sys.path.insert(0,'/workspace/shadowveil/eyes/staged/diagonals')
from PIL import Image, ImageDraw, ImageFont
import render_eyes, render_diag
from crops import crop, B, W, H, Z, A
OUT=os.path.dirname(os.path.abspath(__file__)); os.makedirs(f'{OUT}/tiles',exist_ok=True)
TW,TH=W*Z,H*Z   # 400x220 tiles
# fixed view-space zoom: benchmark inter-eye ~97 src px in a 200 px window -> rig window 144x80 view px (apose eyes 71 px apart);
# diagonal turn frames are x1.54468 smaller than view px -> 93x52 frame px. All tiles scaled to 400x220.
WIN={'apose':(681,222,144,80),'315':(406,170,93,52),'045':(362,170,93,52)}
def rig_tile(view,p):
    if view=='apose': im=render_eyes.render('apose',p)[...,:3]
    else: im,_=render_diag.render(view,p)
    cx,cy,w,h=WIN[view]
    return Image.fromarray(im).crop((cx-w//2,cy-h//2,cx+w//2,cy+h//2)).resize((TW,TH),Image.LANCZOS)

SA=json.load(open(f'{OUT}/source_art.json'))   # shape -> availability (written by hand from inspection, see REPORT.md)
T=json.load(open(f'{OUT}/targets_in.json'))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14); fb=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',15)
NW=780; HDR=30
S=Image.new('RGB',(TW*2+NW,HDR+TH*len(T)),'white'); d=ImageDraw.Draw(S)
for x,t in ((4,'benchmark crop (target only, fixed zoom)'),(TW+4,'rig at closest settings (same view-space zoom)'),(2*TW+8,'note / gaps (rig cannot)')): d.text((x,7),t,font=fb,fill=(0,0,0))
out=[]
for r,t in enumerate(T):
    i=t['n']-1; c,box=crop(i); c.save(f'{OUT}/tiles/{B[i][0]}_bench.png')
    rt=rig_tile(t['view'],t['params']); rt.save(f'{OUT}/tiles/{B[i][0]}_rig.png')
    y=HDR+r*TH; S.paste(c,(0,y)); S.paste(rt,(TW,y))
    p=t['params']; fr=lambda v: round((1-v)*7)
    lines=[f"{t['n']} {t['name']}  view: {t['view']}",
           f"EyeROpen {p['EyeROpen']} (lid {fr(p['EyeROpen'])})  EyeLOpen {p['EyeLOpen']} (lid {fr(p['EyeLOpen'])})",
           f"EyeBallX {p['EyeBallX']}  EyeBallY {p['EyeBallY']}", 'gaps:']
    for g in t['gaps']:
        a=SA.get(g['shape'],{}); tag={'her_sheet':'her art','clean_room':'Clean room','to_be_made':'TO BE MADE'}.get(a.get('status'),'') if a else ''
        if tag in ('her art','Clean room') and t['view']!='apose': tag=f"front: {tag}; {t['view']}: TO BE MADE"
        lines.append(f"- {g['what']}" + (f"  [{tag}]" if tag else ''))
    ty=y+6
    for k,l in enumerate(lines):
        d.text((2*TW+8,ty),l,font=fb if k==0 else font,fill=(0,0,0) if not l.startswith('-') else (150,0,0)); ty+=18 if k==0 else 17
    d.line([(0,y+TH-1),(S.width,y+TH-1)],fill=(180,180,180))
    out.append(dict(t,benchmark=dict(file=A+B[i][1]+'.jpg',crop_box=list(box),zoom=Z,note='target only; pixels never used in any part'),
                    tiles=dict(bench=f'eyes/qa/benchmark_targets/tiles/{B[i][0]}_bench.png',rig=f'eyes/qa/benchmark_targets/tiles/{B[i][0]}_rig.png'),
                    gaps=[dict(g,source_art=SA.get(g['shape'])) for g in t['gaps']]))
S.save(f'{OUT}/sheet.png')
json.dump(dict(generated='2026-10-03 PT by Eyes',params_rule='lid frame = round((1-Open)*7); iris offset per rig.json irisOffsetRule (diagonals: per-eye limits, frame px)',
               benchmarks=out,source_art=SA),open(f'{OUT}/targets.json','w'),indent=1)
print('wrote sheet.png targets.json')
