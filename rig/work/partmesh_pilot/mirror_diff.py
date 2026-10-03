# Python pmpy mirror vs browser (LP solo, quality=linear) for the meshed hair parts; also rigid RD mirror vs browser rigid.
import sys,json,numpy as np; from PIL import Image
sys.path.insert(0,'/workspace/shadowveil/hair/tools'); import render as RD; import pmpy
hd='/workspace/shadowveil/views/apose/hair'; parts,ymax=RD.load_rig('apose',hd)
imgs={p['id']:RD.premul(np.array(Image.open(f"{hd}/{p['file']}").convert('RGBA'))) for p in parts}
PM=pmpy.PM('/workspace/shadowveil/rig/partmesh/staged/apose_hair_strand_03.json'); H,W=next(iter(imgs.values())).shape[:2]; res={}
for mode in ('mesh','rigid'):
  for pid in ('strand_03','strand_03_tip'):
    for s in ((0,1,-1) if mode=='mesh' else (1,-1)):
      Ms=RD.matrices(parts,ymax,s,0); box=(0,0,W,H)
      P=PM.warp(pid,imgs[pid],Ms,box) if (mode=='mesh' and not PM.ident(pid,Ms)) else RD.warp(imgs[pid],Ms[pid],box)
      U=RD.unpremul(P).round().clip(0,255).astype(int)
      f=f"mirror_check/{'rigid/' if mode=='rigid' else ''}browser_{pid}_{s}.png"; B=np.array(Image.open(f).convert('RGBA')).astype(int)
      Ua=U[...,3]; Ba=B[...,3]; da=np.abs(Ua-Ba); dc=np.abs(U[...,:3]-B[...,:3]).max(-1)*((Ua>0)&(Ba>0))
      ink=lambda X:(X[...,3]>=128)&(X[...,:3].max(-1)<=110)
      res[f'{mode}:{pid}:s={s}']=dict(px_alpha_diff_gt0=int((da>0).sum()),px_alpha_diff_gt8=int((da>8).sum()),px_alpha_diff_gt32=int((da>32).sum()),max_alpha_diff=int(da.max()),max_rgb_diff=int(dc.max()),
        ink_px_mirror=int(ink(U).sum()),ink_px_browser=int(ink(B).sum()),ink_xor=int((ink(U)^ink(B)).sum()),alpha_px_browser=int((Ba>0).sum()))
json.dump(res,open('mirror_check/mirror_vs_browser.json','w'),indent=1)
for k,v in res.items(): print(k,v)
