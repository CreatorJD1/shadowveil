import json
S={'rest':(0,0),'M':(0,-1),'smile':(0,1),'OH_half':(0.5,-1),'AA_half':(0.5,0),'EE_half':(0.5,1),'OH':(1,-1),'AA':(1,0),'EE':(1,1)}
seq=[]  # (start,shape)
t=0.0
seq.append((t,'rest')); t=0.6
for s in ['M','smile','OH_half','AA_half','EE_half','OH','AA','EE','rest']:
    seq.append((round(t,4),s)); t+=0.8
# talk pass on 125 ms beat, no EE/smile, close ~every 3-4 beats
talk=['AA_half','AA','OH_half','rest','AA','AA_half','OH','M','AA_half','AA','rest',
      'OH_half','AA','AA_half','M','AA','OH','AA_half','rest','AA_half','AA','OH_half','M','rest']
t0=round(t,4)
for i,s in enumerate(talk): seq.append((round(t0+i*0.125,4),s))
end=round(t0+len(talk)*0.125+0.6,4)
seq.append((round(t0+len(talk)*0.125,4),'rest'))
eps=0.001
O=[];F=[]
for i,(ts,s) in enumerate(seq):
    o,f=S[s]
    if i>0:
        po,pf=S[seq[i-1][1]]
        O.append([round(ts-eps,4),po]);F.append([round(ts-eps,4),pf])
    O.append([ts,o]);F.append([ts,f])
O.append([end,0]);F.append([end,0])
clip={'keys':{'MouthOpen':O,'MouthForm':F},'fps':30,'duration':end,'loop':False,'interp':'linear',
 'notes':'hard steps (1 ms ramps, never sampled at 30 fps). 0-7.8 s: rest then each of 9 shapes held 0.8 s; %.2f-%.2f s: talk pass on 125 ms beat, no EE/EE_half/smile; ends at exact rest. Mouth only; all other params default.'%(t0,t0+len(talk)*0.125),
 'sections':[{'name':'shape_grid','start':0.0,'end':t0},{'name':'talk','start':t0,'end':round(t0+len(talk)*0.125,4)},{'name':'settle_rest','start':round(t0+len(talk)*0.125,4),'end':end}],
 'views':['apose','tpose','left','right','back (no mouth, skip or hold)']}
json.dump({'format':'shadowveil idle clips v1 (same schema as body_tools/idle/idle_clips.json)','spec':'value(t)=linear interpolation of keys[param]; params not listed stay default','generator':'python3 mouth/showcase/make_mouth_showcase.py','clips':{'mouth_showcase':clip}},open('mouth_showcase.json','w'),indent=1)
# validate: sample at 30fps, nearest shape, count switches and hold lengths
def val(k,t):
    for a,b in zip(k,k[1:]):
        if a[0]<=t<=b[0]: return a[1]+(b[1]-a[1])*((t-a[0])/(b[0]-a[0]) if b[0]>a[0] else 0)
    return k[-1][1]
names=list(S)
def near(o,f): return min(names,key=lambda n:((S[n][0]-o)**2+(S[n][1]-f)**2, n!='rest'))
fr=[near(val(O,i/30),val(F,i/30)) for i in range(int(end*30)+1)]
runs=[];c=fr[0];n=0
for x in fr:
    if x==c:n+=1
    else: runs.append((c,n));c=x;n=1
runs.append((c,n))
print('duration',end,'frames',len(fr),'switches',len(runs)-1)
print('grid order',[r[0] for r in runs[:11]])
print('min hold ms',min(r[1] for r in runs[1:-1])*1000/30,'shapes used in talk',sorted(set(talk)))
print('start',fr[0],'end',fr[-1],'MouthOpen range',min(v for _,v in O),max(v for _,v in O),'Form range',min(v for _,v in F),max(v for _,v in F))
