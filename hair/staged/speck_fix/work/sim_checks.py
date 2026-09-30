# Scratch simulation checks for the staged speck fix (reads overlays under /tmp, never writes to the live tree).
#   python3 sim_checks.py <out.json>
# (a) staged strands differ from live ONLY at the speck px, and there they equal base.png exactly (RGBA)
# (b) speck px left behind at sway: speck px where the body layer is still opaque and no hair part drawn above the body
#     covers it (alpha>=128), s in {-1,-.5,.5,1} x HairSwayY in {-1,0,1}; for the current body and the rebuilt scratch body
# (c) hair over eyes/mouth: union over s (41 values in [-1,1]) x HairSwayY {-1,0,1} of hair (layer>=200) coverage (alpha>0) on
#     the eye/mouth parts (alpha>0, not dilated): staged minus live = NEW px.
import sys, json, glob, numpy as np
sys.path.insert(0,'/workspace/shadowveil/hair/tools'); import render as RD
from PIL import Image
R='/workspace/shadowveil'; ST=R+'/hair/staged/speck_fix'; T='/tmp/speckwork'
V=['apose','tpose','left','right','back']; out={}
def A(p): return np.array(Image.open(p).convert('RGBA'))
for v in V:
    o=out[v]={}
    base=A(f'{R}/views/{v}/base.png'); add=np.array(Image.open(f'{ST}/for_base_body/{v}_speck_px_ADD.png'))>127
    parts,ymax=RD.load_rig(v); H,W=add.shape
    # (a)
    bad=0; nfiles=0
    for p in parts:
        sp=f'{ST}/views/{v}/hair/{p["file"]}'
        try: s=A(sp)
        except FileNotFoundError: continue
        nfiles+=1; l=A(f'{R}/views/{v}/hair/{p["file"]}'); d=(s!=l).any(-1)
        bad+=int((d&~add).sum())+int((d&add&~(s==base).all(-1)).sum())
    o['staged_files']=nfiles; o['staged_px_changed']=int(add.sum()); o['px_changed_outside_specks_or_not_exact']=bad
    ys,xs=np.nonzero(add); box=(max(0,xs.min()-40),max(0,ys.min()-40),min(W,xs.max()+41),min(H,ys.max()+41)); x0,y0,x1,y1=box
    sub=add[y0:y1,x0:x1]
    for tag,hd,body in (('current_body',f'{T}/ov_staged/views/{v}/hair',f'{R}/views/{v}/base_body_skin.png'),
                        ('rebuilt_body',f'{T}/ov_staged_rebuilt/views/{v}/hair',f'{T}/ov_staged_rebuilt/views/{v}/base_body_skin.png')):
        ba=A(body)[y0:y1,x0:x1,3]; pts,ym=RD.load_rig(v,hd); worst=0; per={}
        for sx in (-1,-.5,.5,1):
            for sy in (-1,0,1):
                Ms=RD.matrices(pts,ym,sx,sy); cov=np.zeros(sub.shape)
                for p in pts:
                    if p['layer']>=200: cov=np.maximum(cov,RD.warp(RD.premul(A(f"{hd}/{p['file']}")),Ms[p['id']],box)[...,3])
                n=int((sub&(ba>0)&(cov<128)).sum()); per[f'{sx:+g},{sy:+d}']=n; worst=max(worst,n)
        o[f'left_behind_{tag}']=dict(max=worst,per_s=per)
    # (c)
    face=np.zeros((H,W),bool)
    for sub_,pat in (('eyes','Eye*_*.png'),('mouth','*.png')):
        for f in glob.glob(f'{R}/views/{v}/{sub_}/{pat}'):
            if 'chroma' not in f: face|=A(f)[...,3]>0
    if not face.any(): o['face_new_px']=0; o['face_px_live']=0; o['face_px_staged']=0; print(v,o,flush=True); continue
    fy,fx=np.nonzero(face); fb=(max(0,fx.min()-2),max(0,fy.min()-2),min(W,fx.max()+3),min(H,fy.max()+3))
    fsub=face[fb[1]:fb[3],fb[0]:fb[2]]; U={}
    for tag,hd in (('live',f'{R}/views/{v}/hair'),('staged',f'{T}/ov_staged/views/{v}/hair')):
        pts,ym=RD.load_rig(v,hd); u=np.zeros(fsub.shape,bool); cache={p['id']:RD.premul(A(f"{hd}/{p['file']}")) for p in pts if p['layer']>=200}
        for sx in np.round(np.linspace(-1,1,41),3):
            for sy in (-1,0,1):
                Ms=RD.matrices(pts,ym,sx,sy)
                for p in pts:
                    if p['layer']>=200: u|=(RD.warp(cache[p['id']],Ms[p['id']],fb)[...,3]>0)&fsub
        U[tag]=u
    o['face_px_live']=int(U['live'].sum()); o['face_px_staged']=int(U['staged'].sum()); o['face_new_px']=int((U['staged']&~U['live']).sum())
    print(v,{k:(x if not isinstance(x,dict) else x['max']) for k,x in o.items()},flush=True)
json.dump(out,open(sys.argv[1],'w'),indent=1)
