import numpy as np; from PIL import Image, ImageDraw
L=lambda f:Image.open(f).convert('RGBA')
def sheet(rows,cols,crop,scale,out,title):
  cw,ch=(crop[2]-crop[0])*scale,(crop[3]-crop[1])*scale; lab=18
  S=Image.new('RGB',(150+len(cols)*(cw+6),lab+20+len(rows)*(ch+lab)),'white'); d=ImageDraw.Draw(S); d.text((4,2),title,fill='black')
  for j,c in enumerate(cols): d.text((150+j*(cw+6),20),c,fill='black')
  for i,(rn,imgs) in enumerate(rows):
    y=lab+20+i*(ch+lab); d.text((4,y+ch//2),rn,fill='black')
    for j,f in enumerate(imgs):
      im=L(f).crop(crop).resize((cw,ch),Image.NEAREST); bg=Image.new('RGBA',im.size,(200,230,255,255)); bg.alpha_composite(im); S.paste(bg.convert('RGB'),(150+j*(cw+6),y))
  S.save(out); print(out,S.size)
ss=['-1.015','-1','-0.5','0','0.5','1','1.015']
sheet([('rigid (live)',[f'hair_full_rigid/full_{s}.png' for s in ss]),('partmesh',[f'hair_full_pm/full_{s}.png' for s in ss])],[f's={s}' for s in ss],(560,235,655,355),3,'contact_hair_strand03.png','apose strand_03 + tip, HairSwayX=s, quality=linear (bg light blue = transparent). |s|>1 clamps to 1 in the uniform slider path.')
cases=['rest','curl_0.50','curl_0.70','curl_0.87','curl_1.00','pose_Fist','pose_Point','pose_Peace']
A=[np.array(L(f'r_base_data/{c}.png'))[...,3] for c in cases]; dm=np.zeros_like(A[0],bool)
for c in cases[1:]: dm|=np.abs(np.array(L(f'r_base_data/{c}.png')).astype(int)-np.array(L('r_base_data/rest.png')).astype(int)).max(-1)>0
D=np.zeros_like(dm)
for c in cases: D|=np.abs(np.array(L(f'r_final/{c}.png')).astype(int)-np.array(L(f'r_base_data/{c}.png')).astype(int)).max(-1)>0
ys,xs=np.nonzero(D); print('mesh-vs-rigid diff bbox',xs.min(),xs.max(),ys.min(),ys.max())
cx,cy=(xs.min()+xs.max())//2,(ys.min()+ys.max())//2; box=(cx-45,cy-45,cx+45,cy+45)
sheet([('rigid (live)',[f'r_base_data/{c}.png' for c in cases]),('partmesh (4,4,3)',[f'r_final/{c}.png' for c in cases])],cases,box,3,'contact_hand_R_Middle.png','tpose R_Middle1/2/3, rigid vs partmesh final (blend px M1=4 M2=4 M3=3), quality=linear')
