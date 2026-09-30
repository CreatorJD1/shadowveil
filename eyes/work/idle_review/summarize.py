import json,glob,numpy as np
P=json.load(open('params.json'))
S={}
for f in sorted(glob.glob('res_*.json')):
    d=json.load(open(f)); n=d['name']; fr=d['frames']; eyes=[e for e in ('EyeR','EyeL') if e in fr[0]]
    kmis=[r['i'] for r in fr if any(r[e]['k']!=r['k'][0 if e=='EyeR' else 1] for e in eyes)]
    omis=[(r['i'],r['rule'],[(r[e]['dx'],r[e]['dy']) for e in eyes]) for r in fr if r['k']==[0,0] and any((r[e]['dx'],r[e]['dy'])!=tuple(r['rule']) for e in eyes)]
    offs=[]; prev=None
    for r in fr:
        o=tuple((r[e]['dx'],r[e]['dy']) for e in eyes) if r['k']==[0,0] else None
        if o is not None and o!=prev: offs.append((r['i'],o)); prev=o
    rot=[r['face'][2] for r in fr]; tx=[r['face'][0] for r in fr]; ty=[r['face'][1] for r in fr]
    row=dict(kmis=kmis[:20],omis=omis[:10],offsets=offs,face_dx=[round(min(tx),2),round(max(tx),2)],face_dy=[round(min(ty),2),round(max(ty),2)],face_rot=[round(min(rot),2),round(max(rot),2)])
    for e in eyes:
        sl=np.array([r[e]['slide'] if r[e]['slide'][0] is not None else [np.nan,np.nan] for r in fr],float)
        err=np.array([r[e]['err'] for r in fr]); b=np.array([r[e]['bad20'] for r in fr])
        row[e]=dict(slide_max=np.nanmax(np.abs(sl),0).round(2).tolist(),slide_p95=np.nanpercentile(np.abs(sl),95,0).round(2).tolist(),
            err_med=round(float(np.median(err)),2),err_max=round(float(err.max()),2),err_argmax=int(err.argmax()),bad_max=int(b.max()),bad_argmax=int(b.argmax()),
            alphaHole=int(max(r[e]['alphaHole'] for r in fr)),newWhite=int(max(r[e]['newWhite'] for r in fr)),
            newWhite_frames=[r['i'] for r in fr if r[e]['newWhite']>0][:20])
    S[n]=row; print(n,json.dumps(row))
json.dump(S,open('summary.json','w'))
