import json,numpy as np,os
OUT='/workspace/shadowveil/mouth/work/idle_qa/data';IDLE='/workspace/shadowveil/rig/previews/idle'
V=['apose','tpose','left','right'];C=['idle_breathe','idle_weight_shift','idle_arm_settle','auto']
def runs(mask):
    r=[];i=0;n=len(mask)
    while i<n:
        if mask[i]:
            j=i
            while j+1<n and mask[j+1]: j+=1
            r.append((i,j));i=j+1
        else:i+=1
    return r
res={}
for v in V:
  for c in C:
    mdir=f'{IDLE}/frames/{v}' if c=='auto' else f'{IDLE}/frames/keys_{c}_{v}'
    meta=json.load(open(mdir+'/meta.json'));mf=meta['frames']
    pr=[b for b in meta['info']['bones'] if b['id']=='head'][0]['pivot']
    ang=np.array([f['bones']['head'][2] for f in mf]);axis=np.abs(ang)<1e-9
    rig_sw=[(i,mf[i-1]['mouth'][6:],mf[i]['mouth'][6:]) for i in range(1,len(mf)) if mf[i]['mouth']!=mf[i-1]['mouth']]
    R={}
    for src in ('mp4','png'):
        d=json.load(open(f'{OUT}/{src}_{c}_{v}.json'));fr=d['frames'];ax0,ay0=d['anchor']
        md=np.array([[x['mdx'],x['mdy']] for x in fr]);nd=np.array([[x['ndx'],x['ndy']] for x in fr])
        dface=np.hypot(*md.T);dnose=np.hypot(*(md-nd).T)
        te=[]
        for x,m in zip(fr,mf):
            px,py,an=m['bones']['head'];th=np.radians(an)
            ex=px+np.cos(th)*(ax0-pr[0])-np.sin(th)*(ay0-pr[1]);ey=py+np.sin(th)*(ax0-pr[0])+np.cos(th)*(ay0-pr[1]);te.append(np.hypot(ex-x['ax'],ey-x['ay']))
        headtravel=np.hypot(np.array([x['ax'] for x in fr])-ax0,np.array([x['ay'] for x in fr])-ay0)
        r=dict(n=len(fr),headTravelMaxPx=round(float(headtravel.max()),2),headAngleRange=[round(min(x['ang'] for x in fr),3),round(max(x['ang'] for x in fr),3)],
          trackerVsRigHeadPx=round(float(max(te)),2),minHeadCC=min(x['cc'] for x in fr),minMouthCC=min(x['mcc'] for x in fr),
          driftFaceMax=round(float(dface.max()),3),driftFaceMaxFrame=int(dface.argmax()),driftNoseMax=round(float(dnose.max()),3),driftNoseMaxFrame=int(dnose.argmax()),
          driftFaceP95=round(float(np.percentile(dface,95)),3),
          bluePx=sum(x['blue'] for x in fr),blueMaxExcess=round(max(x['blueMax'] for x in fr),1))
        sl=np.array([x['sharpLip'] for x in fr]);sh=np.array([x['sharpHead'] for x in fr])
        r['sharpHeadAxis']=round(float(sh[axis].mean()),4) if axis.any() else None;r['sharpHeadRot']=round(float(sh[~axis].mean()),4)
        r['sharpLipAxis']=round(float(sl[axis].mean()),4) if axis.any() else None;r['sharpLipRot']=round(float(sl[~axis].mean()),4)
        ok=~axis.copy()
        if c!='auto': ok[[81,143,144]]=False
        else:
            bb=[x['best'] for x in fr]; ok&=np.array([0<i<239 and bb[i-1]==bb[i]==bb[i+1] for i in range(len(bb))])
        r['sharpLipRotMin']=round(float(sl[ok].min()),4);r['sharpLipRotMinFrame']=int(np.where(ok,sl,9).argmin())
        r['sharpLipRotP5']=round(float(np.percentile(sl[~axis],5)),4)
        conf=np.array([x['mcc'] for x in fr])>=0.95
        r['driftFaceMaxConfident']=round(float(dface[conf].max()),3);r['driftFaceMaxConfidentFrame']=int(np.where(conf,dface,-1).argmax());r['lowConfidenceMouthFrames']=int((~conf).sum())
        if c!='auto':
            a=np.array([x['a'] for x in fr]);lo=np.median(a[10:70]);hi=np.median(a[95:135]);an=(a-lo)/(hi-lo)
            st=an>0.5;cr=[]
            for i in range(1,len(an)):
                if st[i]!=st[i-1]:
                    fx=i-1+(0.5-an[i-1])/(an[i]-an[i-1]);cr.append(dict(frame=i,dir='rest->smile' if st[i] else 'smile->rest',a_prev=round(float(an[i-1]),3),a=round(float(an[i]),3),tVideoCross=round(fx/30,4),tAnimCross=round(fx/30,4)))
            r['switches']=cr;r['fadeFrames']=[int(i) for i in np.nonzero((an>0.25)&(an<0.75))[0]]
            r['otherShapeBest']=sorted(set(x['best'] for x in fr)-{'rest','smile'})
            r['aNormRange_heldRest']=[round(float(an[:75].min()),3),round(float(an[:75].max()),3)]
        else:
            b=[x['best'] for x in fr];raw=sum(1 for i in range(1,len(b)) if b[i]!=b[i-1])
            seg=[];i=0
            while i<len(b):
                j=i
                while j+1<len(b) and b[j+1]==b[i]: j+=1
                seg.append((b[i],i,j));i=j+1
            held=[s for s in seg if s[2]-s[1]+1>=2];single=[s for s in seg if s[2]==s[1]]
            m=[held[0]] if held else []
            for s in held[1:]:
                if s[0]!=m[-1][0]: m.append(s)
            r['rawLabelChanges']=raw;r['singleFrameLabels']=len(single);r['heldSwitches']=len(m)-1
            r['holdsFrames']=[s[2]-s[1]+1 for s in seg]
        R[src]=r
    R['rig']=dict(switches=rig_sw,nSwitchFrames=len(rig_sw),holdLogLen=len(meta['holds']),minHoldMs=round(min(meta['holds']),1) if meta['holds'] else None,
                  axisAlignedFrames=[int(i) for i in np.nonzero(axis)[0]],axisRuns=runs(list(axis)),sharpToggles=int(sum(axis[i]!=axis[i-1] for i in range(1,len(axis)))))
    res[f'{c}_{v}']=R
json.dump(res,open('/workspace/shadowveil/mouth/work/idle_qa/results.json','w'),indent=1,default=int)
for k,R in res.items():
    p,m=R['png'],R['mp4']
    print(f"{k:24s} drift face/nose mp4 {m['driftFaceMax']}/{m['driftNoseMax']} png {p['driftFaceMax']}/{p['driftNoseMax']} trk {p['trackerVsRigHeadPx']} travel {p['headTravelMaxPx']} blue {m['bluePx']}/{p['bluePx']} bx {p['blueMaxExcess']} lipS ax/rot {p['sharpLipAxis']}/{p['sharpLipRot']} min {p['sharpLipRotMin']}@{p['sharpLipRotMinFrame']} toggles {R['rig']['sharpToggles']} axisRuns {R['rig']['axisRuns']}")
    if 'switches' in p: print('   sw mp4',[(s['frame'],s['dir'],s['tVideoCross'],s['a']) for s in m['switches']],'png',[(s['frame'],s['tVideoCross']) for s in p['switches']],'fade',p['fadeFrames'],m['fadeFrames'],'other',p['otherShapeBest'],'rig',R['rig']['switches'])
    else: print('   auto raw',p['rawLabelChanges'],m['rawLabelChanges'],'single',p['singleFrameLabels'],'held',p['heldSwitches'],m['heldSwitches'],'rig',R['rig']['nSwitchFrames'],R['rig']['holdLogLen'],R['rig']['minHoldMs'])
