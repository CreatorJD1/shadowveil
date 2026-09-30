import numpy as np,json
from PIL import Image,ImageDraw
FR='/workspace/shadowveil/reference/apose_turn/frames'
J={r['f']:r for r in json.load(open('sweep2.json'))}
AF=[('0','f001'),('45','f035'),('90','f057'),('135','f086'),('180','f109'),('225','f133'),('270','f164'),('315','f189')]
Z=3; CW=150; CH=150
def crop(im,h,cxy=None):
    if h: x,y=h['wrist']; ax=np.array(h['axis']); c=np.array([x,y])+ax*h['L']*0.5
    else: c=np.array(cxy)
    b=(int(c[0]-CW/2),int(c[1]-CH/2)); t=im.crop((b[0],b[1],b[0]+CW,b[1]+CH)).resize((CW*Z,CH*Z),Image.LANCZOS); d=ImageDraw.Draw(t)
    if h:
        P=lambda p:((p[0]-b[0])*Z,(p[1]-b[1])*Z)
        w=P(h['wrist']); d.ellipse((w[0]-5,w[1]-5,w[0]+5,w[1]+5),outline='red',width=2)
        e=P(np.array(h['wrist'])+np.array(h['axis'])*h['L']); d.line([w,e],fill='yellow',width=1)
        if h['palm_len']:
            pl=np.array(h['wrist'])+np.array(h['axis'])*h['palm_len']; nv=np.array([-h['axis'][1],h['axis'][0]])
            d.line([P(pl-nv*25),P(pl+nv*25)],fill='cyan',width=1)
        for tp in h['tip_pts']: q=P(tp); d.ellipse((q[0]-4,q[1]-4,q[0]+4,q[1]+4),fill='lime')
    return t,d
def main(rows,fname,title):
    W=Image.new('RGB',(200+2*CW*Z,len(rows)*CH*Z+30),'black'); D=ImageDraw.Draw(W); D.text((5,5),title,fill='white')
    for k,(lab,f) in enumerate(rows):
        r=J[f]; im=Image.open(f'{FR}/{f}.png').convert('RGB'); y=30+k*CH*Z
        th=im.resize((192,292)); W.paste(th,(4,y)); D.text((6,y+300),f'{f}  target {lab}  est {r["theta"]}',fill='white')
        # her R shown in left column, her L in right column
        for col,s in enumerate('RL'):
            h=r['hands'].get(s)
            MAN={'f057':('L',(422,540)),'f164':('R',(351,535))}
            if f in MAN:
                ns,cxy=MAN[f]
                if s==ns: t,d=crop(im,None,cxy); d.text((6,6),f'her {s} (near): lies on hip/thigh, NOT separable from body silhouette',fill='white')
                else: t=Image.new('RGB',(CW*Z,CH*Z),(40,40,40)); d=ImageDraw.Draw(t); d.text((6,6),f'her {s} (far): occluded behind body',fill='white')
            elif h is None:
                t,d=crop(im,None,(r['cx']+(-60 if (s=='R')==(r['theta']<90 or r['theta']>270) else 60),560)); d.text((6,6),f'her {s}: no separable arm component (profile overlap)',fill='white')
            else:
                t,d=crop(im,h)
                pl=h['palm_len']; d.text((6,6),f"her {s}  tips {h['tips']}  L {h['L']:.0f}px  palm {('%.0f'%pl) if pl else '-'}px  pw {('%.0f'%h['palm_w']) if h['palm_w'] else '-'}px  thumb {h['thumb_side']} (exp {h['thumb_expected']})",fill='white')
            W.paste(t,(200+col*CW*Z,y))
    W.save(fname)
if __name__=='__main__':
    import sys
    main(AF,'turn_hands_sheet.png','apose-turn angle frames. col1 = her R hand, col2 = her L hand (3x). red=wrist cut, yellow=axis/L, cyan=palm/finger web line, green=fingertips')
    sw=[(J[f]['theta'],f) for f in [f'f{i:03d}' for i in range(1,242,5)]]
    main([(str(t),f) for t,f in sw[:25]],'turn_sweep_a.png','sweep every 5 frames (f001-f121)')
    main([(str(t),f) for t,f in sw[25:]],'turn_sweep_b.png','sweep every 5 frames (f126-f241)')
