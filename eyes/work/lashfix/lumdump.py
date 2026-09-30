import pickle,numpy as np,sys
v,e=sys.argv[1:3]
g=pickle.load(open(f'tmp/g_{v}_{e}.pkl','rb'))
lum=g['lum'];m=g['mask'];cov=g['cover']|g['crease']|g['lash']
ys,xs=np.nonzero(cov);Y0,Y1,X0,X1=ys.min()-1,ys.max()+1,xs.min()-1,xs.max()+1
print(v,e,X0,'skin',g['skin'],'lash',g['lashcolor'],'c0c1',g['c0'],g['c1'])
for y in range(Y0,Y1+1):
  print('%3d '%y+''.join('M' if m[y,x] else (str(min(9,int(lum[y,x]//15))) if cov[y,x] else ('-' if lum[y,x]>100 else '#')) for x in range(X0,X1+1)))
