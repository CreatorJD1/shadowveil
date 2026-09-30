import sys,json,numpy as np
from PIL import Image
from scipy import ndimage as ndi
from rigrender2 import render,joints,preset
hd=sys.argv[1]; V='apose'
def pose(name,c):
    v=preset(name) if name!='Half' else preset('Fist')
    for k in v: v[k]=v[k]*c
    return v
worst=[]; rows=[]
for name in ['Fist','Point','Peace','Half']:
    for c in [0,0.25,0.5,0.75,1.0]:
        cc=c*0.5 if name=='Half' else c
        v=pose(name,cc)
        # render hands only (transparent base) to test coverage at joints
        out,rig,M,PV,CP=render(V,v,hd,base='base_body.png')
        only,_,_,_,_=render(V,v,hd,base='../../hands/work/_blank.png')
        a=np.array(only)[...,3]
        js=joints(rig,M,PV,CP); mg=max(j[2] for j in js)
        # coverage: disk r=2 around each joint point must be fully opaque in hands-only composite; plus a
        # connectivity test: parent+child union alpha>128 connected
        bad=[]
        for par,ch,g,pt in js:
            x,y=int(round(pt[0])),int(round(pt[1]))
            dsk=a[y-2:y+3,x-2:x+3]
            if dsk.min()<200: bad.append((ch,int(dsk.min())))
        rows.append((name,c,round(mg,3),bad)); 
for r in rows: print(r)
