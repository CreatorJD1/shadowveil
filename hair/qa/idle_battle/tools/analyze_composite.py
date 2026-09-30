# Per-tile hair checks on the side-by-side composites (tiles = per-view mp4 scaled to 682x870, hstack; rows vstacked)
import sys,json
from common import *
vid=sys.argv[1]; name=sys.argv[2]; rowsdef=json.loads(sys.argv[3])   # [[clipprefix or "",...rows]]
views=['apose','tpose','left','right','back']; TW,TH,SH=682,870,240
sx,sy=TW/VW,TH/VH; S=np.diag([sx,sy,1.0]); Si=np.linalg.inv(S)
VV={v:View(v) for v in views}
def half(s,m):
    full=np.zeros((VH,VW),np.uint8); full[s.y0:s.y1,s.x0:s.x1]=m.astype(np.uint8)
    return cv2.resize(full,(TW,TH),interpolation=cv2.INTER_NEAREST)[:SH]
HM={v:dict(M=half(VV[v],VV[v].Mhead),B=half(VV[v],VV[v].boxmask),S=half(VV[v],VV[v].sil),box={k:half(VV[v],m) for k,m in VV[v].boxm.items()}) for v in views}
metas={}
for r,pre in enumerate(rowsdef):
    for v in views:
        mn=(f'keys_{pre}_{v}' if pre else v); m=json.load(open(f'{IDLE}/frames/{mn}/meta.json'))
        metas[(r,v)]=[(f['bones'].get('head') or f['bones'].get('torso'))[2] for f in m['frames']]; del m
nr=len(rowsdef); W_=TW*5
if nr==1: fc=f'crop={W_}:{SH}:0:0'
else: fc=f"split={nr}"+''.join(f'[s{r}]' for r in range(nr))+';'+';'.join(f'[s{r}]crop={W_}:{SH}:0:{r*TH}[c{r}]' for r in range(nr))+';'+''.join(f'[c{r}]' for r in range(nr))+f'vstack={nr}'
cmd=['nice','-n','10','ffmpeg','-v','error','-threads','1','-i',vid,'-filter_complex',fc,'-f','rawvideo','-pix_fmt','rgb24','-']
import subprocess
p=subprocess.Popen(cmd,stdout=subprocess.PIPE); n=W_*SH*nr*3
res={f'{r}_{v}':[] for r in range(nr) for v in views}; rest={}
i=0
while True:
    b=p.stdout.read(n)
    if len(b)<n: break
    fr=np.frombuffer(b,np.uint8).reshape(SH*nr,W_,3)
    for r in range(nr):
        for t,v in enumerate(views):
            img=np.ascontiguousarray(fr[r*SH:(r+1)*SH,t*TW:(t+1)*TW]); s=VV[v]
            Hm=S@rotAt(PIV[0],PIV[1],metas[(r,v)][min(i,239)])@Si
            if i==0:
                full=np.full((VH,VW,3),128,np.uint8); full[s.y0:s.y1,s.x0:s.x1]=s.base_comp
                rr=cv2.resize(full,(TW,TH),interpolation=cv2.INTER_AREA)[:SH]
                rest[(r,v)]={'white':cls_white(rr),'blue':cls_blue(rr),'grey':cls_grey(rr),'hl':s.hairlike(rr)}
            Mw=warp(HM[v]['M'],Hm,TW,SH,True)>0; Bw=warp(HM[v]['B'],Hm,TW,SH,True)>0; Sw=warp(HM[v]['S'],Hm,TW,SH,True)>0
            out={'frame':i}
            for c_,fn in (('white',cls_white),('blue',cls_blue),('grey',cls_grey)):
                rc=warp(rest[(r,v)][c_].astype(np.uint8),Hm,TW,SH,True)
                new=fn(img)&Mw&~Bw&~(cv2.dilate(rc,disk(1))>0)
                if c_=='grey': out['grey_in']=int((new&Sw).sum()); out['grey_out']=int((new&~Sw).sum())
                else: out[c_]=int(new.sum())
                if c_!='grey' or True:
                    lab,nn=nd.label(new&(Sw if c_=='grey' else True)); out[c_+'_blob']=int(max(nd.sum(new,lab,range(1,nn+1))) if nn else 0)
            rh=warp(rest[(r,v)]['hl'].astype(np.uint8),Hm,TW,SH,True)
            nh=s.hairlike(img)&~(cv2.dilate(rh,disk(1))>0)
            out['vid']={k:int((nh&(warp(m,Hm,TW,SH,True)>0)).sum()) for k,m in HM[v]['box'].items()}
            res[f'{r}_{v}'].append(out)
    i+=1
p.wait()
json.dump(dict(video=vid,rows=rowsdef,frames=i,res=res),open(f'{OUT}/data/composite_{name}.json','w'))
print(name,i,'frames done')
