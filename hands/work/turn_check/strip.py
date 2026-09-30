import cv2,numpy as np
from PIL import Image,ImageDraw
V='/workspace/shadowveil/reference/grok_build/public/clean-room/videos/apose-turn.mp4'
cap=cv2.VideoCapture(V); th=[]; i=0
while True:
    ok,f=cap.read()
    if not ok: break
    if i%8==0:
        im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((128,195)); ImageDraw.Draw(im).text((2,2),str(i),fill='white'); th.append(im)
    i+=1
print('frames',i)
cols=16; o=Image.new('RGB',(cols*129,((len(th)+cols-1)//cols)*196))
for k,t in enumerate(th): o.paste(t,((k%cols)*129,(k//cols)*196))
o.save('/workspace/gb/turn_strip.png')
