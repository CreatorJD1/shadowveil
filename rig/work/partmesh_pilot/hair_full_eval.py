import json,numpy as np; from PIL import Image; from scipy import ndimage as ndi
L=lambda f:np.array(Image.open(f).convert('RGBA')).astype(int); res={}
base=L('/workspace/shadowveil/views/apose/base.png') if __import__('os').path.exists('/workspace/shadowveil/views/apose/base.png') else None
def holes(a): t=a<255; lab,n=ndi.label(t); border=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]])); return np.isin(lab,[i for i in range(1,n+1) if i not in border])
for s in ['0','0.5','-0.5','1','-1','1.015','-1.015']:
  A=L(f'hair_full_pm/full_{s}.png'); B=L(f'hair_full_rigid/full_{s}.png')
  reg=np.zeros(A.shape[:2],bool)
  for pid in ('strand_03','strand_03_tip'):
    for d in ('mirror_check','mirror_check/rigid'):
      for ss in ('1','-1'):
        try: reg|=L(f'{d}/browser_{pid}_{ss}.png')[...,3]>0
        except FileNotFoundError: pass
  reg|=L('mirror_check/browser_strand_03_0.png')[...,3]>0; reg|=L('mirror_check/browser_strand_03_tip_0.png')[...,3]>0
  reach=ndi.binary_dilation(reg,iterations=25)
  diff=(np.abs(A-B).max(-1)>0)
  hA,hB=holes(A[...,3]),holes(B[...,3])
  r=dict(changed_px=int(diff.sum()),changed_px_outside_strand03_reach=int((diff&~reach).sum()),
    new_seethrough_px=int(((A[...,3]<B[...,3])&reach).sum()),enclosed_hole_px_pm=int(hA.sum()),enclosed_hole_px_rigid=int(hB.sum()),new_enclosed_hole_px=int((hA&~hB).sum()))
  if s=='0' and base is not None: r['pm_vs_base_px']=int((np.abs(A-base).max(-1)>0).sum())
  res[s]=r; print(s,r)
json.dump(res,open('hair_full_eval.json','w'),indent=1)
