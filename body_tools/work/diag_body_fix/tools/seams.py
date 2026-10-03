import sys; sys.path.insert(0,'.'); from posekit import *
st4 = ndi.generate_binary_structure(2,1)
def seam_ends(ang, pj, img, jn):
    C=ctx(ang); figure = C['fg'] | C['TM']
    owner=np.full((H,W),'',object)
    for k in pj['layerOrder_backToFront']: owner[img[k][...,3]>0]=k
    j=pj['joints'][jn]; ch,par=j['flap_on'],j['under']
    if jn=='head_neck': ch,par='head','neck'
    a=owner==ch; b=owner==par
    seam=(a&ndi.binary_dilation(b,st4))|(b&ndi.binary_dilation(a,st4))
    nearbg=ndi.binary_dilation(~figure,np.ones((5,5)))
    e=seam&nearbg; lab,n=ndi.label(ndi.binary_dilation(e,np.ones((5,5)))); out=[]
    for i in range(1,n+1):
        m=e&(lab==i)
        if m.sum(): ys,xs=np.nonzero(m); out.append([round(float(xs.mean()+.5),1),round(float(ys.mean()+.5),1),int(m.sum())])
    return out
if __name__=='__main__':
    for ang in ('045','315'):
        pj,img=load_set(ORIG+'/'+ang)
        for jn in pj['joints']:
            if 'joint_radius_px' in pj['joints'][jn]: print(ang,jn,pj['joints'][jn]['pivot'],seam_ends(ang,pj,img,jn))
