# Diagonal-frame selection (Base Body). Reads frames + views, writes only into diagonals/.
import sys, json, math, numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE='/workspace/shadowveil/body_tools/work/apose_turn'; sys.path.insert(0,HERE)
from seg import mask_of
from measure import measure, runs
R='/workspace/shadowveil'; FR=R+'/reference/apose_turn/frames/f%03d.png'
AM=json.load(open(HERE+'/angle_map.json')); HO=AM['handoff']
TM={int(x['f']):x for x in json.load(open(HERE+'/turn_measure.json'))['frames']}
def lerp(a,b,t): return a+(b-a)*t
# handoff for a diagonal = mean of the two neighbouring sharp-view handoffs (scale, dx, dy); sole target 1681.5 avg
NB={45:('apose','left'),135:('left','back'),225:('back','right'),315:('right','apose')}
def view_mask(v): return np.array(Image.open(f'{R}/views/{v}/base.png'))[...,3]>0
def arm_angles(m, o):
    out={}
    for sd,a in o['arms'].items():
        (ax,ay),(tx,ty)=a['armpit'],a['tip']
        out[sd]=round(math.degrees(math.atan2(abs(tx-ax),(ty-ay))),1)
    return out
def hand_info(m,o):
    # hand = bottom 18% of the separated arm run (armpit->tip). clear = outer run separate from torso run on every hand row; gap = min px gap
    H=o['H']; res={}
    cx=o['cx']
    for sd in ('R','L'):
        a=o['arms'].get(sd)
        if not a: res[sd]={'clear':False,'gap_min_px':0,'note':'arm merged into torso (not separable)'}; continue
        ty=a['tip'][1]; y0=int(ty-0.07*H); gaps=[]; widths=[]; nruns=[]
        for y in range(y0,ty+1):
            rr=runs(m[y]); t=[r for r in rr if r[0]<=cx<=r[1]]
            if not t: continue
            t=t[0]
            outer=[r for r in rr if (r[1]<t[0] if sd=='R' else r[0]>t[1])]
            if not outer: gaps.append(0); continue
            r=outer[-1] if sd=='R' else outer[0]  # run nearest the torso
            gaps.append((t[0]-r[1]-1) if sd=='R' else (r[0]-t[1]-1)); nruns.append(len(outer))
        g=min(gaps) if gaps else 0
        res[sd]={'clear':bool(g>=2),'gap_min_px':int(g),'tip':a['tip'],'max_outer_runs':max(nruns) if nruns else 0}
    return res
def sharp(path,m):
    g=np.array(Image.open(path).convert('L')).astype(float)
    lap=nd.laplace(g); edge=nd.binary_dilation(m,iterations=2)^nd.binary_erosion(m,iterations=2)
    inner=nd.binary_erosion(m,iterations=4)
    return round(float(lap[inner].var()),1), round(float(np.abs(lap[edge]).mean()),2)
def iou(a,b): return float((a&b).sum()/max(1,(a|b).sum()))
def to_view(m,s,dx,dy):
    im=Image.fromarray((m*255).astype(np.uint8)).transform((1365,1739),Image.AFFINE,(1/s,0,-dx/s,0,1/s,-dy/s),resample=Image.BILINEAR)
    return np.array(im)>127
VM={v:view_mask(v) for v in ('apose','left','right','back')}
VO={v:measure(VM[v]) for v in VM}
VARM={v:arm_angles(VM[v],VO[v]) for v in VM}
CENT={45:33,135:87,225:131,315:191}
rows={}
for ang,c in CENT.items():
    va,vb=NB[ang]; hs=lerp(HO[va]['scale'],HO[vb]['scale'],.5); hdx=lerp(HO[va]['dx'],HO[vb]['dx'],.5); hdy=lerp(HO[va]['dy'],HO[vb]['dy'],.5)
    lst=[]
    for f in range(c-4,c+5):
        p=FR%f; m=mask_of(p); o=measure(m)
        # per-frame uniform fit: top->40, sole->1682 (45/315, like apose) or 1681 (135/225, like back/profiles)
        SOLE=1682 if ang in (45,315) else 1681
        s=(SOLE-40)/o['H']; dy=40-s*o['top']
        # fixed-handoff residuals (interp of neighbour views)
        top_h=hs*o['top']+hdy; sole_h=hs*o['foot']+hdy
        # dx: centre hip-band x on view centre 682 (diagonal has no sharp counterpart; use mean of neighbour hip cx)
        vcx=(VO[va]['cx']+VO[vb]['cx'])/2; dx=vcx-s*o['cx']
        vm=to_view(m,s,dx,dy)
        ia,ib=iou(vm,VM[va]),iou(vm,VM[vb])
        aa=arm_angles(m,o); hi=hand_info(m,o); lv,ev=sharp(p,m)
        tm=TM.get(f,{})
        lst.append(dict(frame=f,angle_est=tm.get('angle_best'),angle_range=tm.get('angle_range_abs'),raw_top=o['top'],raw_sole=o['foot'],raw_H=o['H'],
            fit=dict(scale=round(s,5),dx=round(dx,2),dy=round(dy,2)),
            handoff_interp=dict(scale=round(hs,5),dx=round(hdx,2),dy=round(hdy,2),H_view=round(hs*o['H'],1),top_view=round(top_h,1),sole_view=round(sole_h,1),
                                 H_err=round(hs*o['H']-(SOLE-40),1),sole_err=round(sole_h-SOLE,1)),
            iou_neighbour_views={va:round(ia,3),vb:round(ib,3)},
            arm_angle_deg=aa,hands=hi,lap_var_inner=lv,edge_lap=ev,aa_band=tm.get('q',{}).get('aa_band_px_per_edge_px')))
    rows[ang]=lst
json.dump(dict(view_arm_angle_deg=VARM,view_measure={v:{k:VO[v][k] for k in ('top','foot','H','cx')} for v in VO},rows=rows),open(HERE+'/diagonals/_analysis.json','w'),indent=1)
print('views arm', VARM)
for ang,l in rows.items():
    print('==',ang)
    for r in l:
        h=r['hands']; print(r['frame'],r['angle_est'],'H',r['raw_H'],'sole',r['raw_sole'],'Hv',r['handoff_interp']['H_view'],'solev',r['handoff_interp']['sole_view'],'iou',r['iou_neighbour_views'],'arm',r['arm_angle_deg'],
          'hR',h['R']['clear'],h['R']['gap_min_px'],'hL',h['L']['clear'],h['L']['gap_min_px'],'lap',r['lap_var_inner'],r['edge_lap'],'aa',r['aa_band'])
