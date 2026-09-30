import lashgeo,numpy as np,sys,pickle
v,e=sys.argv[1],sys.argv[2]
g=lashgeo.geom(v,e)
keep={k:g[k] for k in ['mask','band','aa','cover','crease','lash','fwd','fwd_cover','eye_region','linepx','lum','rgb','top','bot','cols','c0','c1','side','skin','lashcolor','bb','hair_sw','crease_rgb','dark_unconn','skin_d','Ue','lower','wide','th']}
pickle.dump(keep,open(f'tmp/g_{v}_{e}.pkl','wb'))
m=g['mask'];ys,xs=np.nonzero(g['cover']|g['crease']|g['lash']); 
Y0,Y1,X0,X1=ys.min()-2,ys.max()+2,xs.min()-2,xs.max()+2
print(v,e,'x',X0,'c0c1',g['c0'],g['c1'],'side',g['side'])
for y in range(Y0,Y1+1):
    s=''
    for x in range(X0,X1+1):
        if m[y,x]: ch='M'
        elif g['lash'][y,x]: ch='W'
        elif g['fwd'][y,x]: ch='F'
        elif g['band'][y,x]: ch='B'
        elif g['aa'][y,x]: ch='a'
        elif g['crease'][y,x]: ch='c'
        elif g['cover'][y,x]: ch='L' if g['linepx'][y,x] else 'o'
        elif g['lum'][y,x]<85: ch='#'
        elif g['linepx'][y,x]: ch=':'
        else: ch='.'
        s+=ch
    print('%3d '%y+s)
