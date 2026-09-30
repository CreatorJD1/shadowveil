# analyse hidden (rest-covered) palm pixels over the curl range: poke (exposed outside the posed silhouette), useful (fills a gap), boundary/interior
import sys,json,numpy as np
from PIL import Image
from scipy import ndimage as nd
from qalib import *
def analyse(view,S,runs,C,A):
    hid=C&(A>0);poke=np.zeros_like(hid);use=np.zeros_like(hid);edge=np.zeros_like(hid);exp=np.zeros_like(hid);gap=np.zeros_like(hid);expf2=np.zeros_like(hid)
    visPalm=(A>0)&~C
    for D in runs:
        r=Run(D)
        for cn in [c for c in r.C if c.startswith('curl_')]:
            ps=r.parts(cn,S);fing=np.zeros_like(hid)
            for p in ps:
                if not p.endswith('_palm'): fing|=r.layer(cn,p)[...,3]>=128
            sil=nd.binary_fill_holes(nd.binary_closing(visPalm|fing,structure=disk(2)))
            ex=~fing
            poke|=hid&ex&~sil
            use|=hid&ex&sil
            gap|=C&(A<255)&ex&sil&~fing     # not-yet-opaque palm spots that would fill a gap
            edge|=hid&ex&sil&nd.binary_dilation(~sil,structure=np.ones((5,5)))
            exp|=hid&ex
            if float(cn[5:])>=0.875: expf2|=C&ex
    return dict(hid=hid,poke=poke,use=use,edge=edge,exp=exp,gap=gap,expf2=expf2)
