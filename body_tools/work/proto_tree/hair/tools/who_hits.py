import sys,glob,os,json,numpy as np
sys.argv_saved=sys.argv; 
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0,'/workspace/shadowveil/hair/tools'); from render import matrices,load_rig,R
exec(open('/workspace/shadowveil/hair/validate_hair.py').read().split('report={}')[0].split('FIX=')[0])  # imports
src=open('/workspace/shadowveil/hair/validate_hair.py').read()
ns={}; exec(src[src.index('def mul'):src.index('report={}')],globals())
v=sys.argv_saved[1]; pids=sys.argv_saved[2].split(','); deg=float(sys.argv_saved[3]) if len(sys.argv_saved)>3 else None
parts,ymax=load_rig(v)
if deg is not None:
    for p in parts:
        if p['id'] in pids: p['maxSwayDeg']=deg
for pid in pids:
    m=np.array(Image.open(f'{R}/views/{v}/hair/{pid}.png'))[...,3]>0
    for f in sorted(glob.glob(f'{R}/views/{v}/eyes/Eye*_*.png')+glob.glob(f'{R}/views/{v}/mouth/*.png')):
        if 'chroma' in f: continue
        F=ndi.binary_dilation(np.array(Image.open(f).convert('RGBA'))[...,3]>0,iterations=2)
        tot=0
        for sx in np.linspace(-1,1,41):
            M=matrices(parts,ymax,sx,0)[pid]; w,_=affmask(m,M)
            for dy in (-3,0,3): tot+=int((shifted(w,dy)&F).sum())
        if tot: print(v,pid,os.path.basename(f),tot)
