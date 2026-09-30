import json,glob,sys,numpy as np
sys.path.insert(0,'/workspace/shadowveil/hair/qa/idle_battle/tools')
from common import available_names
D='/workspace/shadowveil/hair/qa/idle_battle/data'
BLOB=3   # a check-1 hit needs a connected blob >= 3 px (1-2 px isolated specks = H.264 noise)
out={}
names=available_names()
for n in names:
    d=json.load(open(f'{D}/{n}.json')); R=d['rows']; o={}
    # check 1
    c1={}
    for k in ('white','blue','grey_in','grey_out'):
        hits=[r for r in R if r['c1_'+k+'_blob']>=BLOB]
        c1[k]=dict(frames=len(hits),max_px=max((r['c1_'+k] for r in R),default=0),max_blob=max((r['c1_'+k+'_blob'] for r in R),default=0),
                   worst=(lambda r:dict(frame=r['frame'],t=r['t'],video_t=r['video_t'],px=r['c1_'+k],blob=r['c1_'+k+'_blob'],bbox=r.get('c1_'+k+'_bbox')))(max(R,key=lambda r:(r['c1_'+k+'_blob'],r['c1_'+k]))),
                   hit_frames=[r['frame'] for r in hits])
    o['c1']=c1
    o['c1_pass']=all(c1[k]['frames']==0 for k in ('white','blue','grey_in'))
    # check 2
    f0=R[0]['vid']
    clean=[r for r in R if not(r['lid'] or r['iris'] or r['mouth_change'])]
    o['c2']=dict(geo_max=max(sum(r['geo'].values()) for r in R),geo_any_max=max(sum(r['geo_any'].values()) for r in R),
                 vid_clean_max={k:max(r['vid'][k] for r in clean) for k in f0},vid_all_max={k:max(r['vid'][k] for r in R) for k in f0},vid_f0=f0,
                 vid_clean_worst=(lambda r:dict(frame=r['frame'],t=r['t'],vid=r['vid']))(max(clean,key=lambda r:sum(r['vid'].values()))) if f0 else None)
    o['c2_pass']=o['c2']['geo_max']==0
    # check 3
    bg=np.array([r['bun_geo'] for r in R]); bv=np.array([r['bun_vid'][:2] for r in R]); av=np.array([r['anchor_vid'][:2] for r in R])
    rel=bv-av; gm=np.hypot(bg[:,0],bg[:,1]); vm=np.hypot(rel[:,0],rel[:,1])
    o['c3']=dict(geo_max_px=float(gm.max()),geo_max_frame=int(gm.argmax()),vid_max_px=float(vm.max()),vid_max_frame=int(vm.argmax()),vid_max_t=R[int(vm.argmax())]['t'],
                 anchor_resid_max=float(np.hypot(av[:,0],av[:,1]).max()),gap_px_max=max(r['bun_gap'] for r in R),
                 bun_match_q_max=max(r['bun_vid'][2] for r in R),world_head_deg=[min(r['head_deg'] for r in R),max(r['head_deg'] for r in R)])
    # check 4
    ax=np.array([r['head_axis'] for r in R]); sb=np.array([r['sharp_band'] for r in R]); sc=np.array([r['sharp_ctrl'] for r in R]); ss=np.array([r['sharp_strand'] for r in R])
    dpb=np.array([r['dprev_band'] for r in R])
    tog=[i for i in range(1,len(R)) if ax[i]!=ax[i-1]]
    sharp_frames=[int(i) for i in np.nonzero(ax)[0]]
    c4=dict(sharp_frames=sharp_frames,toggles=tog,toggle_t=[R[i]['t'] for i in tog])
    if ax.any() and (~ax).any():
        # compare sharp frames to the soft frames immediately around them (+-3), frame 0 excluded
        nb=sorted(set(j for i in sharp_frames if i>0 for j in range(max(1,i-3),min(len(R),i+4)) if not ax[j]))
        sf=[i for i in sharp_frames if i>0]
        if sf:
            c4.update(hair_edge_grad_sharp=float(sb[sf].mean()),hair_edge_grad_soft=float(sb[nb].mean()),hair_edge_ratio=float(sb[sf].mean()/sb[nb].mean()),
                  face_grad_ratio=float(sc[sf].mean()/sc[nb].mean()) if sc[nb].mean()>0 else None,strand_grad_ratio=float(ss[sf].mean()/ss[nb].mean()),
                  band_diff_at_toggles=float(dpb[tog].mean()),band_diff_other_median=float(np.median(np.delete(dpb[1:],[t-1 for t in tog]))))
    o['c4']=c4
    # check 5
    tips={}
    for k in d['tips']:
        g=np.array([r['tips'][k] for r in R]); v=np.array([r['tips_vid'][k][:2] for r in R])
        loc=np.hypot(g[:,0],g[:,1]); wor=np.hypot(g[:,2],g[:,3]); vv=np.hypot(v[:,0],v[:,1])
        tips[k]=dict(local_max=float(loc.max()),local_max_frame=int(loc.argmax()),world_max=float(wor.max()),vid_local_max=float(vv.max()),
                     local_series=[round(float(x),3) for x in g[:,0]])
    o['tips']=tips
    o['t0']=R[0]['t']
    out[n]=o
comp={}
for f in sorted(glob.glob(f'{D}/composite_*.json')):
    d=json.load(open(f)); res={}
    for k,L in d['res'].items():
        res[k]=dict(white=max(x['white_blob'] for x in L),blue=max(x['blue_blob'] for x in L),grey_in_blob=max(x['grey_blob'] for x in L),grey_in=max(x['grey_in'] for x in L),
                    grey_in_frames=sum(1 for x in L if x['grey_blob']>=BLOB),grey_out=max(x['grey_out'] for x in L),vid=max(sum(x['vid'].values()) for x in L),vid_f0=sum(L[0]['vid'].values()),
                    worst_grey_in=max(L,key=lambda x:x['grey_blob'])['frame'])
    comp[f.split('composite_')[1][:-5]]=dict(rows=d['rows'],frames=d['frames'],res=res)
json.dump(dict(per_video=out,composites=comp),open(f'{D}/aggregate.json','w'),indent=1)
