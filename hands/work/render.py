import json, numpy as np
from PIL import Image, ImageDraw
ROOT='/workspace/shadowveil'; W,Hh=1365,1739
def T(x,y): return np.array([[1,0,x],[0,1,y],[0,0,1]],float)
def Rz(deg):
    t=np.deg2rad(deg); c,s=np.cos(t),np.sin(t); return np.array([[c,-s,0],[s,c,0],[0,0,1]],float)
def load_rig(v):
    rig=json.load(open(f'{ROOT}/views/{v}/hands/rig.json'))
    imgs={}
    for p in rig['parts']:
        if p['file']: imgs[p['id']]=Image.open(f'{ROOT}/views/{v}/hands/{p["file"]}').convert('RGBA')
    return rig,imgs
def angles(rig,params):
    """params: dict like {'HandRIndex1':1.0,'HandRSpread':.5,'HandRThumbSpread':-1}"""
    ang={}
    for p in rig['parts']:
        pid=p['id']; side,nm=pid.split('_')
        a=0.0
        if nm!='palm' and p.get('maxCurlDeg'):
            a+=params.get(f'Hand{side}{nm}',0.0)*p['maxCurlDeg']
        ang[pid]=a
    for key,sp in rig['spread'].items():
        val=params.get(key,0.0)
        if 'fingers' in sp:
            for f,fs in sp['fingers'].items(): ang[fs['part']]+=val*fs['maxSpreadDeg']
        else:
            ang[sp['part']]+= val*(sp['degAtPlus1'] if val>=0 else -sp['degAtMinus1'])
    return ang
def world(rig,ang):
    byid={p['id']:p for p in rig['parts']}; M={}
    def get(pid):
        if pid in M: return M[pid]
        p=byid[pid]; par=get(p['parent']) if p['parent'] else np.eye(3)
        if p['pivotX'] is None: M[pid]=par; return par
        m=par@T(p['pivotX'],p['pivotY'])@Rz(ang[pid])@T(-p['pivotX'],-p['pivotY']); M[pid]=m; return m
    for pid in byid: get(pid)
    return M
def render(v,base,params=None,skip_hidden=True):
    rig,imgs=load_rig(v); params=params or {}
    ang=angles(rig,params); M=world(rig,ang)
    out=base.copy()
    for p in sorted(rig['parts'],key=lambda p:p['layer']):
        if p['id'] not in imgs: continue
        if skip_hidden and p.get('hidden'): continue
        im=imgs[p['id']]; m=M[p['id']]
        if np.allclose(m,np.eye(3)): out.alpha_composite(im); continue
        inv=np.linalg.inv(m); co=tuple(inv[0].tolist()+inv[1].tolist())
        out.alpha_composite(im.convert('RGBa').transform((W,Hh),Image.AFFINE,co,resample=Image.BILINEAR).convert('RGBA'))
    return out,rig,M
