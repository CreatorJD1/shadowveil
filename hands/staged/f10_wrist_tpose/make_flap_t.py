# F10 staged T-pose (from F7 make_flap.py) palm flaps.  make_flap.py <out dir> <radius px> [line px=2] [depth px=99]
# Flap = px on the forearm side of Base Body's wrist cut line, within <radius> of the palm pivot and <depth> of the line,
# under Body's forearm piece where it is alpha 255 (so fully covered at rest), and transparent in the live palm.
# Fill = her flat skin (186,129,85); the flap's outer boundary (every flap px 8-adjacent to px that are neither hand nor flap), <line px> deep,
# = her line colour (13,11,29). The seam side touching her hand gets no line. Only <S>_palm.png changes; nothing inside hands/tpose_hand_erase_mask.png.
import sys,json,os,numpy as np
from PIL import Image
from scipy import ndimage as nd
OUT,RAD=sys.argv[1],float(sys.argv[2]);LW=int(sys.argv[3]) if len(sys.argv)>3 else 2;DEP=float(sys.argv[4]) if len(sys.argv)>4 else 99
B='/workspace/shadowveil/body_tools/work/hairless_division_staged/tpose/';H='/workspace/shadowveil/views/tpose/hands/';os.makedirs(OUT,exist_ok=True)
SKIN=(186,129,86);LINE=(13,8,21);K8=np.ones((3,3),bool);hm=np.array(Image.open('/workspace/shadowveil/hands/tpose_hand_erase_mask.png').convert('L'))>0
rig=json.load(open(H+'rig.json'));log={}
handall=np.zeros(hm.shape,bool)
for p in rig['parts']:
    if p.get('file'): handall|=np.array(Image.open(H+p['file']).convert('RGBA'))[...,3]>0
for S in 'LR':
    W=json.load(open(B+f'wrist_line_{S}.json'));(x0,y0),(x1,y1)=W['line'];px,py=W['pivot'];fa=np.array(Image.open(B+f'pieces/forearm_{S}.png').convert('RGBA'))
    t=np.array([x1-x0,y1-y0]);t/=np.linalg.norm(t);n=np.array([-t[1],t[0]])
    yy,xx=np.mgrid[:hm.shape[0],:hm.shape[1]];d=(xx+.5-px)*n[0]+(yy+.5-py)*n[1]
    fx,fy=np.nonzero(fa[...,3].T==255)[0][:1],None
    side=np.sign(np.mean(((np.nonzero(fa[...,3]==255)[1]+.5-px)*n[0]+(np.nonzero(fa[...,3]==255)[0]+.5-py)*n[1])))   # forearm side of the line
    d*=side
    a=np.array(Image.open(H+f'{S}_palm.png').convert('RGBA'));b=a.copy()
    flap=(d>0)&(d<=DEP)&((xx+.5-px)**2+(yy+.5-py)**2<=RAD*RAD)&((nd.binary_erosion(fa[...,3]==255,structure=K8,iterations=int(os.environ['ERO']),border_value=0)|((yy+.5>py) if os.environ.get('TOPONLY') else False)) if int(os.environ.get('ERO','0')) else (fa[...,3]==255))&(fa[...,3]==255)&(a[...,3]==0)&~hm&~handall
    lab,nl=nd.label(flap|hm|(a[...,3]>0),structure=K8);keep=np.unique(lab[hm]);flap&=np.isin(lab,keep[keep>0])   # only flap attached to her hand
    b[flap,:3]=SKIN;b[flap,3]=255
    outside=~(flap|handall|(a[...,3]>0));ln=flap&nd.binary_dilation(outside,structure=K8,iterations=LW)
    b[ln,:3]=LINE
    Image.fromarray(b).save(f'{OUT}/{S}_palm.png');ch=(a!=b).any(2)
    log[S]=dict(erode=int(os.environ.get('ERO','0')),erode_top_only=bool(os.environ.get('TOPONLY')),radius=RAD,line_px=LW,depth=DEP,flap_px=int(flap.sum()),line_px_count=int(ln.sum()),changed_in_hand_mask=int((ch&hm).sum()),
                flap_not_under_opaque_forearm=int((flap&(fa[...,3]<255)).sum()));print(S,log[S])
json.dump(log,open(OUT+'/flap_log.json','w'),indent=1)
