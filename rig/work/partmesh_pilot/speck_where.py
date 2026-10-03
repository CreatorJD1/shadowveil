import sys,json,numpy as np;sys.dont_write_bytecode=True
from scipy import ndimage as nd
from pivot_qa_lib import comp_dir
import eval_hand as E
tag=sys.argv[1];base=sys.argv[2] if len(sys.argv)>2 else 'base0030'
la=json.load(open(f'la_{tag}.json'))['cases']
for k in la:
  if not k.startswith('R '):continue
  cn=k.split()[1];ca=np.array(comp_dir(f'r_{tag}',cn,'R')).astype(int);cb=np.array(comp_dir(f'r_{base}',cn,'R')).astype(int)
  reach=nd.binary_dilation(E.middle_reach(f'r_{tag}',cn)|E.middle_reach(f'r_{base}',cn),iterations=2)
  def floating(c):
    ik=(c[...,3]>=128)&(c[...,:3].max(-1)<110);lab,n=nd.label(ik,structure=np.ones((3,3)))
    if n==0:return np.zeros(ik.shape,bool)
    sz=nd.sum(ik,lab,range(1,n+1));big=np.isin(lab,1+np.nonzero(sz>8)[0]);nb=nd.binary_dilation(big,iterations=2);fl=np.zeros_like(ik)
    for i in 1+np.nonzero(sz<=8)[0]:
      cc=lab==i
      if not (cc&nb).any():fl|=cc
    return fl
  s=floating(ca)&~nd.binary_dilation(floating(cb),iterations=2)&reach
  ys,xs=np.nonzero(s);print(cn,list(zip(xs.tolist(),ys.tolist())))
