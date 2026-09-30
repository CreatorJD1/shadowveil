import subprocess,numpy as np,cv2,sys
from common import *
def grab(path,n,w,h,y=0,hh=240):
    cmd=['nice','-n','10','ffmpeg','-v','error','-threads','1','-i',path,'-vf',f'select=eq(n\\,{n}),crop={w}:{hh}:0:{y}','-vframes','1','-f','rawvideo','-pix_fmt','rgb24','-']
    b=subprocess.run(cmd,capture_output=True).stdout; return np.frombuffer(b,np.uint8).reshape(hh,w,3).astype(np.float32)
views=['apose','tpose','left','right','back']
ref={}
for v in views:
    b=np.array(Image.open(f'{P}/views/{v}/base.png').convert('RGBA')).astype(np.float32)
    comp=b[...,:3]*b[...,3:]/255+128*(1-b[...,3:]/255); comp=np.pad(comp,((0,1),(0,1),(0,0)),constant_values=128)
    ref[v]=cv2.resize(comp,(682,870),interpolation=cv2.INTER_AREA)[:240]
f=grab(f'{IDLE}/idle_all.mp4',0,3410,870)
for t in range(5):
    tile=f[:,t*682:(t+1)*682]; e={v:float(np.abs(tile-ref[v]).mean()) for v in views}
    print('idle_all tile',t,min(e,key=e.get),{k:round(x,1) for k,x in e.items()})
# rows of idle_keys_all vs the all5 clips at frame 150
clips=['idle_breathe','idle_weight_shift','idle_arm_settle']
a5={c:grab(f'{IDLE}/keys/{c}_all5.mp4',150,3410,870) for c in clips}
for r in range(3):
    row=grab(f'{IDLE}/keys/idle_keys_all.mp4',150,3410,2610,y=r*870)
    e={c:float(np.abs(row-a5[c]).mean()) for c in clips}; print('keys_all row',r,min(e,key=e.get),{k:round(x,2) for k,x in e.items()})
for c in clips:
    f=grab(f'{IDLE}/keys/{c}_all5.mp4',0,3410,870)
    print(c,[min(views,key=lambda v:np.abs(f[:,t*682:(t+1)*682]-ref[v]).mean()) for t in range(5)])
