import json,glob,os,numpy as np
from PIL import Image, ImageDraw
D='br';res={};rows=[]
L=lambda n: np.asarray(Image.open(f'{D}/{n}.png')).astype(np.int16)
fixv={v:[x['xy'] for x in json.load(open(f'{v}_skin_fix.json'))['generator']['chainBleedFix']['vertices']] for v in ('left','right')}
for v in ('left','right'):
    res[v]={}
    for f in sorted(glob.glob(f'{D}/{v}_live__*.png')):
        p=f.split('__')[1][:-4];a=L(f'{v}_live__{p}');b=L(f'{v}_fix__{p}');ch=(a!=b).any(-1);nh=(b[...,3]==0)&(a[...,3]>0)
        ys,xs=np.nonzero(ch);xy=np.array(fixv[v]) if fixv[v] else np.zeros((0,2))
        # distance of each changed px from the nearest re-weighted vertex (how local the change is)
        dmax=float(np.sqrt(((np.stack([xs,ys],1)[:,None,:]-xy[None])**2).sum(-1)).min(1).max()) if len(xs) else 0.0
        res[v][p]={'px_changed':int(ch.sum()),'new_holes':int(nh.sum()),'max_rgb_delta':int(np.abs(a-b).max()) if ch.any() else 0,'changed_px_max_dist_from_reweighted_verts':round(dmax,1),'bbox':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else None}
        if ch.any():
            cx,cy=int(np.median(xs)),int(np.median(ys));R=40
            def c(im):
                im=im[cy-R:cy+R,cx-R:cx+R].astype(np.uint8);al=im[...,3:4]/255.;return (im[...,:3]*al+230*(1-al)).astype(np.uint8)
            d=c(b).copy();d[ch[cy-R:cy+R,cx-R:cx+R]]=[255,0,255]
            row=np.concatenate([np.kron(x,np.ones((4,4,1),np.uint8)) for x in (c(a),c(b),d)],1)
            lab=Image.fromarray(np.full((row.shape[0],170,3),255,np.uint8));ImageDraw.Draw(lab).text((4,4),f'{v}\n{p}\n{int(ch.sum())} px changed\n{int(nh.sum())} new holes',fill=(0,0,0));rows.append(np.concatenate([np.asarray(lab),row],1))
json.dump(res,open('browser_live_vs_fix.json','w'),indent=1)
if rows:
    hdr=Image.new('RGB',(rows[0].shape[1],22),'white');ImageDraw.Draw(hdr).text((174,5),'live skin.json | --chain-bleed-fix | changed px (magenta)   4x, browser rig (ss2)',fill=(0,0,0))
    Image.fromarray(np.concatenate([np.asarray(hdr)]+rows,0)).save('sheet_live_vs_fix.png')
for v in res:
    for p,r in res[v].items(): print(v,p,r)
