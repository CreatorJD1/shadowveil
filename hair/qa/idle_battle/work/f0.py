import subprocess,numpy as np,sys
from PIL import Image
def frame(path,idx,w=1366,h=1740):
    cmd=['ffmpeg','-v','error','-threads','1','-i',path,'-vf',f'select=eq(n\\,{idx})','-vframes','1','-f','rawvideo','-pix_fmt','rgb24','-']
    b=subprocess.run(cmd,capture_output=True).stdout
    return np.frombuffer(b,np.uint8).reshape(h,w,3)
v=sys.argv[1]; vid=sys.argv[2]
f=frame(vid,0)
b=np.array(Image.open(f'views/{v}/base.png').convert('RGBA')).astype(float)
comp=b[...,:3]*b[...,3:]/255+np.array([128,128,128])*(1-b[...,3:]/255)
print('bg corner video',f[5,5],f[-1,-1], 'rgb under alpha0 in base', b[5,5])
best=None
for dy in range(-2,3):
  for dx in range(-2,3):
    fv=f[2+dy:2+dy+1735,2+dx:2+dx+1361].astype(float); c=comp[2:1737,2:1363]
    e=np.abs(fv-c).mean()
    if best is None or e<best[0]: best=(e,dx,dy)
print(v,'best offset',best)
fv=f[:1739,:1365].astype(float); d=np.abs(fv-comp).max(-1)
print('offset0 mean',d.mean(),'p99',np.percentile(d,99),'head region mean',d[40:350,550:820].mean(), 'n>40 head',(d[40:350,550:820]>40).sum())
