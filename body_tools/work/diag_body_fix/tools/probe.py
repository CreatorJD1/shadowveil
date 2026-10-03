import sys; sys.path.insert(0,'.'); from posekit import *
for ang in ('045','315'):
    C = ctx(ang); F=C['F']; fg=C['fg']
    pj, img = load_set(ORIG+'/'+ang)
    # owner at rest
    own = np.full((H,W),'',object); L={p['id']:p['layer'] for p in pj['pieces']}
    for k in pj['layerOrder_backToFront']:
        m = img[k][...,3]>0; own[m]=k
    for s in 'RL':
        ua = own=='upper_arm_'+s; dt = ndi.distance_transform_edt(ua)
        ys,xs=np.nonzero(ua); top=ys.min()
        sel = ua & (np.mgrid[0:H,0:W][0] < top+60)
        i=np.argmax(np.where(sel,dt,0)); y,x=divmod(i,W); print(ang,'shoulder',s,'old',[p['pivot'] for p in pj['pieces'] if p['id']=='upper_arm_'+s],'dtmax',(x+.5,y+.5),dt[y,x],'top',top)
    # outline width: dark run inward from silhouette edge
    lum=F.sum(2); edge = fg & ndi.binary_dilation(~fg, ndi.generate_binary_structure(2,1))
    dark = fg & (lum<300)
    dd = ndi.distance_transform_edt(fg)
    print(ang,'dark depth hist', [int(((dark)&(np.abs(dd-k)<0.5)).sum()) for k in range(1,6)], 'fg depth counts',[int((fg&(np.abs(dd-k)<0.5)).sum()) for k in range(1,6)])
    # key px near neck gap 045
    key=C['key']; 
    box=(slice(195,240),slice(400,420)); 
    print(ang,'key px in box',int(key[box].sum()),'fg&key',int((fg&key)[box].sum()), 'pieces alpha there', sum(int((img[k][...,3][box]>0).sum()) for k in img))
    a=np.array(Image.open(f'{ORIG}/{ang}/figure_keyed_full.png'))[...,3]; b=np.array(Image.open(f'{ORIG}/{ang}/body_whole_rest.png'))[...,3]
    encl = key & ~ndi.binary_fill_holes(~fg) if False else None
    # enclosed key components (not border-connected) sizes
    lab,n=ndi.label(key); border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))
    for i in range(1,n+1):
        if i in border: continue
        m=lab==i; sz=m.sum()
        if sz>=6:
            ys,xs=np.nonzero(m); print('  enclosed key comp',sz,'x',xs.min(),xs.max(),'y',ys.min(),ys.max(),'in fullfig a>0',int((a[m]>0).sum()),'bodywhole',int((b[m]>0).sum()),'hair',int((C['T']['hair'][m]).sum()))
