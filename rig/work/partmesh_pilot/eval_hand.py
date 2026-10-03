# Pilot pass mark (R hand, T-pose, R_Middle chain) from the Hands owners' lineart.py / pivot_qa.py outputs + composites.
import sys,json,numpy as np
sys.dont_write_bytecode=True
from PIL import Image
from scipy import ndimage as nd
from pivot_qa_lib import comp_dir
def disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1];return x*x+y*y<=r*r
def enclosed(op):
    lab,n=nd.label(~op);b=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])));k=np.ones(n+1,bool);k[list(b)]=False;k[0]=False;return k[lab]
def middle_reach(D,cn):
    m=None
    for s in (1,2,3):
        a=np.array(Image.open(f'{D}/{cn}_layers/R_Middle{s}.png'))[...,3]>0; m=a if m is None else m|a
    return m
def evaluate(tag,base='base_data'):
    la=json.load(open(f'la_{tag}.json'))['cases']; lb=json.load(open(f'la_{base}.json'))['cases']
    pq=json.load(open(f'pq_{tag}.json')); pb=json.load(open(f'pq_{base}.json'))
    meta={c['name']:c for c in json.load(open(f'r_{tag}/meta.json'))['cases']}
    rows={};ok=True
    for k,r in la.items():
        if not k.startswith('R '): continue
        cn=k.split()[1]; J={p:v for p,v in r['joints'].items() if p.startswith('R_Middle')}
        width=max([abs(v['dw']) for v in J.values() if v['dw'] is not None]+[abs(r['finger_dw'].get('Middle') or 0)])
        brk=max([v['new_breaks'] for v in J.values()]+[0]); sharp=max([v['new_sharp'] for v in J.values()]+[0])
        A=comp_dir(f'r_{tag}',cn,'R')[...,3]>=128; B=comp_dir(f'r_{base}',cn,'R')[...,3]>=128
        reach=nd.binary_dilation(middle_reach(f'r_{tag}',cn)|middle_reach(f'r_{base}',cn),iterations=2)
        ha,hb=enclosed(A),enclosed(B); newholes=int((ha&~hb&reach).sum()); newholes_out=int((ha&~hb&~reach).sum())
        ca=np.array(comp_dir(f'r_{tag}',cn,'R')).astype(int); cb=np.array(comp_dir(f'r_{base}',cn,'R')).astype(int)
        def floating(c):
            ik=(c[...,3]>=128)&(c[...,:3].max(-1)<110); lab,n=nd.label(ik,structure=np.ones((3,3)))
            if n==0: return np.zeros(ik.shape,bool)
            sz=nd.sum(ik,lab,range(1,n+1)); big=np.isin(lab,1+np.nonzero(sz>8)[0]); nearbig=nd.binary_dilation(big,iterations=2)
            sm=np.isin(lab,1+np.nonzero(sz<=8)[0]); fl=np.zeros_like(ik)
            for i in 1+np.nonzero(sz<=8)[0]:
                cc=lab==i
                if not (cc&nearbig).any(): fl|=cc
            return fl
        fa,fb=floating(ca),floating(cb); specks=int((fa&~nd.binary_dilation(fb,iterations=2)&reach).sum())
        moved_out=int(((np.abs(ca-cb).max(-1)>0)&~reach).sum())
        st=meta[cn].get('pmStat',{}); outside=max([x['maxVsRigidOutsideBlend'] for x in st.values()]+[0]); inside=max([x['maxVsRigid'] for x in st.values()]+[0])
        hb_=pb.get(k) or pb.get('tpose '+k) ; ha_=pq.get(k) or pq.get('tpose '+k)
        row=dict(width_max_abs_dw=width,middle_breaks=brk,middle_new_sharp=sharp,new_hole_px_in_reach=newholes,new_hole_px_outside=newholes_out,
                 changed_px_outside_middle_reach=moved_out,vertex_disp_outside_blend=outside,vertex_disp_in_blend_max=inside,new_stray_ink_px=specks)
        row['PASS']=width<=1 and brk<2 and sharp==0 and newholes==0 and moved_out==0 and outside<=2 and specks==0
        ok&=row['PASS']; rows[cn]=row
    return ok,rows
if __name__=='__main__':
    for tag in sys.argv[1:]:
        ok,rows=evaluate(tag); print(tag,'PASS' if ok else 'FAIL')
        for cn,r in rows.items(): print('  ',cn,r)
        json.dump(dict(PASS=ok,rows=rows),open(f'eval_{tag}.json','w'),indent=1)
