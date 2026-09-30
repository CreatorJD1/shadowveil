import cv2,numpy as np,json,sys,glob
R='/workspace/shadowveil/rig/previews/idle/frames/'
name,view=sys.argv[1],sys.argv[2]
P=json.load(open('params.json'))[name]['rows']
wr=json.load(open(f'/workspace/shadowveil/views/{view}/eyes/rig.json'))['workRegion']
x0,y0,x1,y1=wr[0],wr[1],wr[2]+1,wr[3]+1
files=sorted(glob.glob(R+f'{name}/frames/f*.png'))
v=[]
for f in files:
    im=cv2.imread(f,cv2.IMREAD_UNCHANGED)[y0:y1,x0:x1,:3]; g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    v.append(float(cv2.Laplacian(g,cv2.CV_64F).var()))
v=np.array(v); ax=[r['ax'] for r in P]
rest=cv2.cvtColor(cv2.imread(R+f'{name}/rest.png',cv2.IMREAD_UNCHANGED)[y0:y1,x0:x1,:3],cv2.COLOR_BGR2GRAY); r0=cv2.Laplacian(rest,cv2.CV_64F).var()
sharpF=[i for i in range(len(v)) if ax[i]]
print(name,'rest lapvar',round(r0),'sharp(axis) frames',sharpF,'lapvar sharp med',round(float(np.median(v[sharpF]))) if sharpF else None,'soft med',round(float(np.median([v[i] for i in range(len(v)) if not ax[i]]))),'min',round(v.min()),'max',round(v.max()))
jumps=[(i,round(v[i-1]),round(v[i])) for i in range(1,len(v)) if abs(v[i]-v[i-1])/max(v[i-1],1)>0.25]
print('  frame-to-frame sharpness jumps >25%:',jumps)
json.dump(dict(lapvar=v.tolist(),axis=ax),open(f'sharp_{name}.json','w'))
