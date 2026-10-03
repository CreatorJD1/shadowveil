import sys,numpy as np; sys.dont_write_bytecode=True
from PIL import Image; from scipy import ndimage as nd; from pivot_qa_lib import comp_dir
exec(open('eval_hand.py').read().split("def evaluate")[0])
def floating(c):
    ik=(c[...,3]>=128)&(c[...,:3].max(-1)<110); lab,n=nd.label(ik,structure=np.ones((3,3)))
    sz=nd.sum(ik,lab,range(1,n+1)); big=np.isin(lab,1+np.nonzero(sz>8)[0]); nb=nd.binary_dilation(big,iterations=2); fl=np.zeros_like(ik)
    for i in 1+np.nonzero(sz<=8)[0]:
        cc=lab==i
        if not (cc&nb).any(): fl|=cc
    return fl
tag=sys.argv[1]; tiles=[]
for cn in sys.argv[2:]:
    ca=comp_dir(f'r_{tag}',cn,'R').astype(int); cb=comp_dir('r_base_data',cn,'R').astype(int)
    reach=nd.binary_dilation(middle_reach(f'r_{tag}',cn)|middle_reach('r_base_data',cn),iterations=2)
    f=floating(ca)&~nd.binary_dilation(floating(cb),iterations=2)&reach; ys,xs=np.nonzero(f); print(cn,list(zip(xs.tolist(),ys.tolist())), 'darkest', [int(ca[y,x,:3].max()) for y,x in zip(ys,xs)])
    if len(xs):
        x,y=int(xs.mean()),int(ys.mean())
        for c in (cb,ca):
            im=Image.fromarray(c.clip(0,255).astype(np.uint8)).crop((x-15,y-15,x+15,y+15)).resize((240,240),Image.NEAREST); bg=Image.new('RGBA',im.size,(200,230,255,255)); bg.alpha_composite(im); tiles.append(bg)
S=Image.new('RGB',(250*len(tiles),240),'white')
for i,t in enumerate(tiles): S.paste(t.convert('RGB'),(i*250,0))
S.save(f'specks_{tag}.png')
