"""rigrender + contract v1.2 frame objects: frame = floor(curl*2+0.5); per-frame pivot (default part pivot)
and childPivot (default child's pivot). M_child = M_parent . T(childPivot_parent - pivot_child) . rotAt(pivot_child, angle)."""
import json,re,numpy as np
from PIL import Image
from rigrender import rotAt,preset,hand_angle,img,ROOT,W,Hh,PRESETS,FING
RX=re.compile(r'^([LR])_(Thumb|Index|Middle|Ring|Pinky)(\d)$')
def fsel(v,p):
    m=RX.match(p['id']); fr=p.get('frames')
    if not m or not isinstance(fr,list): return None
    c=v.get(f'Hand{m.group(1)}{m.group(2)}',0); k=int(np.floor(c*(len(fr)-1)+0.5)); k=max(0,min(len(fr)-1,k))
    e=fr[k]; return e if isinstance(e,dict) else {'file':e}
def T(dx,dy): return np.array([[1,0,dx],[0,1,dy],[0,0,1.]])
def chain(rig,v):
    by={p['id']:p for p in rig['parts']}; kids={}
    for p in rig['parts']: kids.setdefault(p.get('parent'),p['id'])
    M={}; PV={}; CP={}
    def m(i):
        if i in M: return M[i]
        p=by[i]; e=fsel(v,p) or {}
        pv=np.array(e.get('pivot',[p.get('pivotX') or 0,p.get('pivotY') or 0]),float)
        par=p.get('parent')
        if par in by:
            Mp=m(par); cp=CP[par] if CP[par] is not None else pv
            base=Mp@T(*(cp-pv))
        else: base=np.eye(3)
        M[i]=base@rotAt(pv[0],pv[1],hand_angle(rig,v,p)); PV[i]=pv
        CP[i]=np.array(e['childPivot'],float) if 'childPivot' in e else None   # None -> child attaches at its own pivot
        return M[i]
    for i in by: m(i)
    return M,PV,CP
def render(view,v,handsdir,base='base_body.png'):
    rig=json.load(open(f'{handsdir}/rig.json')); out=img(f'{ROOT}/views/{view}/{base}').copy()
    M,PV,CP=chain(rig,v)
    for p in sorted(rig['parts'],key=lambda p:p['layer']):
        if not p.get('file'): continue
        e=fsel(v,p); fn=f"{handsdir}/{e['file'] if e else p['file']}"
        im=Image.open(fn).convert('RGBA'); m=M[p['id']]
        if np.allclose(m,np.eye(3)): out.alpha_composite(im); continue
        inv=np.linalg.inv(m)
        out.alpha_composite(im.convert('RGBa').transform((W,Hh),Image.AFFINE,tuple(inv[0])+tuple(inv[1]),resample=Image.BILINEAR).convert('RGBA'))
    return out,rig,M,PV,CP
def joints(rig,M,PV,CP):
    """world gap between parent's childPivot and child's pivot (should be 0 by construction) + list of joint world points"""
    by={p['id']:p for p in rig['parts']}; res=[]
    for p in rig['parts']:
        par=p.get('parent')
        if par in by and RX.match(p['id']):
            cpp=CP[par] if CP[par] is not None else np.array([p['pivotX'],p['pivotY']],float)
            a=M[par]@np.r_[cpp,1]; b=M[p['id']]@np.r_[PV[p['id']],1]
            res.append((par,p['id'],float(np.hypot(*(a-b)[:2])),a[:2]))
    return res
