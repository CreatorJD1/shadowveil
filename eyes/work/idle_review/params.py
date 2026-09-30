import json,sys
R='/workspace/shadowveil/rig/previews/idle/'
runs=[(v,v,f'qa/{v}_qa.json') for v in ('apose','tpose','left','right')]+[(f'keys_{c}_{v}',v,f'keys/qa/keys_{c}_{v}_qa.json') for c in ('idle_arm_sway','idle_weight_shift','idle_arm_settle') for v in ('apose','tpose','left','right')]
out={}
for name,v,q in runs:
    m=json.load(open(R+f'frames/{name}/meta.json')); qa=json.load(open(R+q))['frames']
    rows=[]
    for i,(f,g) in enumerate(zip(m['frames'],qa)):
        p=f['params']; hb=f['bones']['head']
        rows.append(dict(i=i,t=f['t'],R=p['EyeROpen'],L=p['EyeLOpen'],X=p['EyeBallX'],Y=p['EyeBallY'],hx=hb[0],hy=hb[1],hr=hb[2],ax=g.get('headAxisAligned'),tor=f['bones']['torso'][2]))
    out[name]=dict(view=v,rows=rows,keys=m.get('keys'))
json.dump(out,open('params.json','w'))
for n,o in out.items():
    r=o['rows']
    cl=[x['i'] for x in r if min(x['R'],x['L'])<1]
    ax=[x['ax'] for x in r]; tog=[i for i in range(1,len(ax)) if ax[i]!=ax[i-1]]
    print(n,'eye<1 frames',cl[:60],'| X range',min(x['X'] for x in r),max(x['X'] for x in r),'Y',min(x['Y'] for x in r),max(x['Y'] for x in r),'| head rot range',round(min(x['hr'] for x in r),4),round(max(x['hr'] for x in r),4),'| axis toggles at',tog)
