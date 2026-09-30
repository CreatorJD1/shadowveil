# Speck sites: BEFORE (current files) vs PROPOSED (simulated only, in a scratch copy: speck px cleared from a scratch base_body and
# cut from base.png into the owning strand). Nothing under views/ or hair/*mask is written.
import sys,json,os,shutil,numpy as np
sys.path.insert(0,'/workspace/shadowveil/hair/tools')
import render as RD
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
P='/workspace/shadowveil'; OUT=P+'/hair/qa/wisp_fix'; WK=OUT+'/work/sim'; os.makedirs(OUT+'/crops',exist_ok=True)
prop=json.load(open(OUT+'/erase_mask_proposal/proposal.json'))
BLUE=(0,0,255); Z=6; summary={}
for v in ['apose','tpose','left','right','back']:
    hd=f'{P}/views/{v}/hair'; sd=f'{WK}/{v}_hair'; shutil.rmtree(sd,ignore_errors=True); shutil.copytree(hd,sd)
    base=np.array(Image.open(f'{P}/views/{v}/base.png').convert('RGBA')); bb=np.array(Image.open(f'{P}/views/{v}/base_body.png').convert('RGBA'))
    bbs=bb.copy()
    rig=json.load(open(hd+'/rig.json'))['parts']; fby={e['id']:e['file'] for e in rig}
    for sid,px in prop[v]['pixels_xy'].items():
        st=np.array(Image.open(f'{sd}/{fby[sid]}').convert('RGBA'))
        for x,y in px: st[y,x]=base[y,x]; bbs[y,x]=0
        Image.fromarray(st).save(f'{sd}/{fby[sid]}')
    bbp=f'{WK}/{v}_base_body_sim.png'; Image.fromarray(bbs).save(bbp)
    summary[v]=[]
    for sid,px in prop[v]['pixels_xy'].items():
        m=np.zeros(base.shape[:2],bool)
        for x,y in px: m[y,x]=True
        lab,n=ndi.label(ndi.binary_dilation(m,iterations=6))
        sites=sorted([(int((m&(lab==k)).sum()),k) for k in range(1,n+1)],reverse=True)[:3]
        for cnt,k in sites:
            ys,xs=np.nonzero(m&(lab==k)); cx,cy=int(xs.mean()),int(ys.mean())
            box=(cx-20,cy-20,cx+21,cy+21)
            RD._cache.clear()
            tiles=[('rest',RD.render(v,0,0,box,bg=BLUE))]
            for sx in (-1,1): tiles.append((f'before s={sx:+d}',RD.render(v,sx,0,box,bg=BLUE)))
            for sx in (-1,1): tiles.append((f'proposed s={sx:+d}',RD.render(v,sx,0,box,hd=sd,body=bbp,bg=BLUE)))
            # stay-behind count: speck px still opaque in the composite at max sway where the strand moved away
            left_behind={}
            parts_,ymax_=RD.load_rig(v)
            for sx in (-1,1):
                Ms=RD.matrices(parts_,ymax_,sx,0)
                sa=RD.warp(RD.premul(np.array(Image.open(f"{hd}/{fby[sid]}").convert('RGBA'))),Ms[sid],box)[...,3]
                mm=m[box[1]:box[3],box[0]:box[2]]
                for tag,bdy in (('before',f'{P}/views/{v}/base_body.png'),('proposed',bbp)):
                    body=np.array(Image.open(bdy))[box[1]:box[3],box[0]:box[2],3]
                    left_behind[f'{tag} s={sx:+d}']=int((mm&(body>0)&(sa<128)).sum())
            W=41*Z; im=Image.new('RGB',(W*len(tiles),W+16),(255,255,255)); d=ImageDraw.Draw(im)
            for i,(t,a) in enumerate(tiles):
                im.paste(Image.fromarray(a[...,:3]).resize((W,W),Image.NEAREST),(i*W,16)); d.text((i*W+3,2),t,fill=(0,0,0))
            fn=f'crops/speck_{v}_{sid}_{cx}_{cy}.png'; im.save(f'{OUT}/{fn}')
            summary[v].append(dict(strand=sid,site_center=[cx,cy],px=cnt,crop=fn,speck_px_left_behind_uncovered=left_behind))
            print(v,sid,cx,cy,cnt,left_behind,flush=True)
json.dump(summary,open(OUT+'/erase_mask_proposal/speck_sites.json','w'),indent=1)
