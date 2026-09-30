import json,sys,numpy as np
d=json.load(open(f'data/{sys.argv[1]}.json'));m=json.load(open(sys.argv[2]))
fr=d['frames'];ax,ay=d['anchor']
err=[];angerr=[]
for x,mf in zip(fr,m['frames']):
    px,py,an=mf['bones']['head']; th=np.radians(an)
    # head pivot in rest = the bone pivot; find bone pivot rest from info
    pr=[b for b in m['info']['bones'] if b['id']=='head'][0]['pivot']
    ex=px+np.cos(th)*(ax-pr[0])-np.sin(th)*(ay-pr[1]); ey=py+np.sin(th)*(ax-pr[0])+np.cos(th)*(ay-pr[1])
    err.append(np.hypot(ex-x['ax'],ey-x['ay'])); angerr.append(x['ang']-an)
print('tracker vs rig head bone @mouth anchor: max px',round(max(err),3),'mean',round(float(np.mean(err)),3),'ang err max',round(float(np.max(np.abs(angerr))),4))
sw=[(x['f'],fr[i-1]['best'],x['best']) for i,x in enumerate(fr) if i and x['best']!=fr[i-1]['best']]
print('switches',sw)
ms=[(mf['frame'],mf['mouth']) for i,mf in enumerate(m['frames']) if i and mf['mouth']!=m['frames'][i-1]['mouth']]
print('meta switches',len(ms),ms[:6])
for x in fr[76:86]+fr[139:146]: print(x['f'],x['best'],x['a'],x['brms'],x['bad'],x['mdx'],x['mdy'],x['sharpHead'],x['sharpLip'],x['ang'])
