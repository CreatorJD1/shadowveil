import numpy as np,json
from PIL import Image
from locate import fg
from arm2 import arms2,wrist2,geoball
from handgeo import handgeo
from shape import shape_metrics
FR='/workspace/shadowveil/reference/apose_turn/frames'
T=json.load(open('theta.json')); S=json.load(open('silhouette.json'))
out=[]
for i in range(241):
    img=np.array(Image.open(f'{FR}/f{i+1:03d}.png').convert('RGB')); m=fg(img); th=T['theta'][i]; H=S[i]['H']; top=S[i]['top']
    ys,xs=np.nonzero(m); cx=float(np.median(xs))
    rec=dict(f=f'f{i+1:03d}',theta=round(th,1),H=H,cx=cx,hands={})
    front=(th<90 or th>270)
    comps=[]
    for fr in (0.30,0.40,0.50):
        for c in arms2(m,top,H,fr):
            if all(np.hypot(c['tip'][0]-q['tip'][0],c['tip'][1]-q['tip'][1])>15 for q in comps): c['fr']=fr; comps.append(c)
    for c in comps:
        gb=geoball(m,c['tip'],int(170*H/1056))
        if gb is None: continue
        c=dict(c,mask=gb,geo_area=int(gb.sum()))
        side_img='imgR' if np.mean(np.nonzero(c['mask'])[1])>cx else 'imgL'
        her=('L' if side_img=='imgR' else 'R') if front else ('R' if side_img=='imgR' else 'L')
        try: wc=wrist2(c,H)
        except ValueError: continue
        g=handgeo(wc['hand'],wc['wrist'],wc['axis']); sm=shape_metrics(wc['hand'],wc['wrist'],wc['axis'])
        exp={'L':'-v','R':'+v'}[her] if front else {'L':'+v','R':'-v'}[her]
        ts=sm['thumb_side'] if abs(sm['bulge_diff'])>0.05*sm['L'] else 'indeterminate'
        if her in rec['hands']: her=her+'?'
        rec['hands'][her]=dict(geo_area=c['geo_area'],fr=c['fr'],img_side=side_img,wrist=wc['wrist'],axis=wc['axis'],wrist_w=wc['wrist_width'],L=g['L'],W=g['W'],tips=g['tips'],tip_pts=g['tip_pts'],palm_len=g['palm_len'],palm_w=g['palm_w'],finger_len=g['finger_len'],valleys=g['valleys'],thumb_side=ts,thumb_expected=exp,bulge=sm['bulge_diff'],area=int(wc['hand'].sum()))
    out.append(rec)
json.dump(out,open('sweep2.json','w'))
f=lambda x:'-' if x is None else round(x,1)
for r in out:
    if int(r['f'][1:])%5!=1 and r['f'] not in ('f035','f057','f086','f109','f133','f164','f189'): continue
    print(r['f'],r['theta'],r['H'],' | '.join(f"{k}:tips{h['tips']} L{f(h['L'])} pl{f(h['palm_len'])} pw{f(h['palm_w'])} fl{f(h['finger_len'])} th{h['thumb_side']}/{h['thumb_expected']}" for k,h in sorted(r['hands'].items())))
