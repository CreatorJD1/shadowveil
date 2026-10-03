import sys; sys.path.insert(0,'/workspace/shadowveil/body_tools/work/round2'); import sim, json, numpy as np
from scipy import ndimage as nd
def holes(c):
    lab,n=nd.label(~c); b=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]]))); return np.isin(lab,[k for k in range(1,n+1) if k not in b])
def run(skinf, meta, frames, roi):
    sk=sim.load_skin(skinf); m=json.load(open(meta)); rest=sim.coverage(sk,m['frames'][0]['bones'] if False else {b['id']:[b['pivot'][0],b['pivot'][1],0] for b in m['info']['bones']},roi)
    rh=nd.binary_dilation(holes(rest),iterations=3); out={}
    for f in frames:
        c=sim.coverage(sk,m['frames'][f]['bones'],roi); out[f]=int((holes(c)&~rh).sum())
    return out
if __name__=='__main__':
    skinf=sys.argv[1]; which=sys.argv[2]
    if which=='arm': r=run(skinf,'render/old_pre6d_base_arm_settle/meta.json',range(158,177),(620,540,780,720))
    else: r=run(skinf,sys.argv[3],range(int(sys.argv[4]),int(sys.argv[5])+1),(640,690,760,900))
    print(sys.argv[1].split('/')[-1],which,'total',sum(r.values()),'peak',max(r.values()),{k:v for k,v in r.items() if v})
