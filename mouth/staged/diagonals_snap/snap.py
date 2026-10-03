# Palette snap for Base Mouth's STAGED diagonal mouth renders (mouth/staged/diagonals/<ang>/renders/*.png -> diagonals_snap/<ang>/renders/).
# Every opaque px more than tol=2 RGB from qa_gates' own diagonal palette (all 5 base.png, her live mouth files in all views,
# her turn frame for that angle, reference/test_sheet_expressions.jpg) is replaced by its nearest palette colour. Alpha untouched.
# Chroma px (B>max(R,G)+60, B>120) would be cleared to alpha 0; there are none in the mouth set. Live files are never touched.
import sys,os,glob,json,shutil
sys.dont_write_bytecode=True;ROOT='/workspace/shadowveil';sys.path.insert(0,ROOT+'/rig');os.chdir(ROOT)
import numpy as np,qa_gates as G
from PIL import Image
from scipy.spatial import cKDTree
OUT='mouth/staged/diagonals_snap';log={}
for ang in ['045','315']:
  os.makedirs(f'{OUT}/{ang}/renders',exist_ok=True)
  for f in sorted(glob.glob(f'mouth/staged/diagonals/{ang}/renders/*.png')):
    img=G.rgba(f).copy();fn=os.path.basename(f);P=G.unpack(G.palette(G.palette_sources(ang,'mouth',fn)));tree=cKDTree(P)
    op=img[...,3]==255;ys,xs=np.nonzero(op);d,i=tree.query(img[ys,xs,:3].astype(int),k=1);bad=d>2.0;ch=[]
    rows=[dict(x=int(x),y=int(y),old=img[y,x,:3].tolist(),new=P[ii].tolist(),dist=round(float(dd),2)) for x,y,ii,dd in zip(xs[bad],ys[bad],i[bad],d[bad])]
    img[ys[bad],xs[bad],:3]=P[i[bad]]
    r,g,b,a=[img[...,k].astype(int) for k in range(4)];cm=(a>=1)&(b>np.maximum(r,g)+60)&(b>120)
    for y,x in zip(*np.nonzero(cm)): ch.append(dict(x=int(x),y=int(y),old=img[y,x].tolist()))
    img[cm]=0
    o=f'{OUT}/{ang}/renders/{fn}'
    if rows or ch: Image.fromarray(img.astype(np.uint8),'RGBA').save(o)
    else: shutil.copyfile(f,o)  # unchanged file: byte copy
    log[f'{ang}/{fn}']=dict(snapped=rows,chroma_cleared=ch,byte_copy=not(rows or ch))
json.dump(log,open(f'{OUT}/snap_log.json','w'),indent=1)
print(sum(len(v['snapped']) for v in log.values()),'px snapped;',sum(len(v['chroma_cleared']) for v in log.values()),'chroma cleared;',sum(v['byte_copy'] for v in log.values()),'files byte-copied')
