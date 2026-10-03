# apose: neck extension under the head for the 9 px head-group stretch (+2 margin): straight outlines x647/x715, flat skin between; hidden at rest
import numpy as np, json
from PIL import Image
T='/workspace/shadowveil/body_tools/work/hairless_division_staged/apose'
n=np.array(Image.open(f'{T}/pieces_pre_headgroup/neck.png')).astype(np.uint8); h=np.array(Image.open(f'{T}/pieces_pre_headgroup/head.png'))
SKIN=np.array([186,129,86,255],np.uint8); LINE=np.array([13,11,29,255],np.uint8)
XL,XR=647,715; EXT=9+2+1   # rows above the lowest head-opaque row per column (stretch 9 + margin 2, +1 so the bottom head row itself is covered)
hid=h[...,3]==255            # neck px under opaque head are invisible at rest
H,W=hid.shape; new=n.copy(); add=np.zeros((H,W),bool); rem=np.zeros((H,W),bool)
Y0,Y1=270,345
for x in range(XL,XR+1):
    col=hid[Y0:Y1,x]; ys=np.nonzero(col)[0]
    if not len(ys): continue
    yb=Y0+ys.max()            # lowest head-opaque row in this column (chin/jaw bottom)
    for y in range(yb-EXT+1,yb+1):
        if not hid[y,x]: continue
        new[y,x]=LINE if x in (XL,XR) else SKIN; add[y,x]=True
# old flap px outside the neck lines that are hidden at rest would show beside the neck at the stretch -> remove (hidden, so rest unchanged)
xx=np.arange(W)[None,:].repeat(H,0); yy=np.arange(H)[:,None].repeat(W,1)
rem=(n[...,3]>0)&hid&((xx<XL)|(xx>XR))&(yy>=Y0)&(yy<Y1)
new[rem]=0
ch=(new!=n).any(-1)
Image.fromarray(new,'RGBA').save(f'{T}/pieces/neck.png')
print(json.dumps({'ext_px_written':int((add&ch).sum()),'line_px':int((add&ch&((xx==XL)|(xx==XR))).sum()),'removed_hidden_px_outside_lines':int(rem.sum()),'changed_px':int(ch.sum()),'changed_not_hidden':int((ch&~hid).sum())}))
