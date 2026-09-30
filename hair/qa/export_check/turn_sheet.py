import numpy as np, json
from PIL import Image, ImageDraw
ROOT='/workspace/shadowveil'; F=ROOT+'/reference/apose_turn/frames'; OUT=ROOT+'/hair/qa/export_check'
C={m['f']:m for m in json.load(open(OUT+'/turn_compare.json'))['video']}
O=json.load(open(OUT+'/turn_compare.json'))['ours']
cols=[(1,0),(25,30),(34,45),(41,60),(61,90),(86,135),(109,180),(132,225),(161,270),(182,300),(191,315),(200,330)]
ours={0:'apose',90:'left',180:'back',270:'right'}
TW,TH=150,190
def head_crop(img,fgmask,figH,scale):
    ys,xs=np.nonzero(fgmask); top=ys.min(); cx=int(np.median(xs[ys<top+int(0.12*figH)]))
    h=int(0.30*figH); w=int(h*TW/TH)
    c=img.crop((cx-w//2,top-int(0.02*figH),cx+w//2,top-int(0.02*figH)+h)).resize((TW,TH),Image.LANCZOS); return c
sheet=Image.new('RGB',(TW*len(cols),TH*2+60),(15,15,15)); D=ImageDraw.Draw(sheet)
D.text((4,2),'top: apose-turn.mp4 frames (shared extract, 24fps), est. yaw (0=front, 90=her left side/face screen-left, 180=back). bottom: our base.png view at the matching yaw. Same crop = 30% of figure height.',fill=(255,255,255))
for k,(f,yaw) in enumerate(cols):
    im=Image.open(f'{F}/f{f:03d}.png').convert('RGB'); a=np.array(im).astype(int)
    bg=(a[...,2]>140)&(a[...,0]<90)&(a[...,1]<90)&(a[...,2]-np.maximum(a[...,0],a[...,1])>90)
    a2=a.copy(); a2[bg]=[60,150,60]; im=Image.fromarray(a2.astype(np.uint8))
    t=head_crop(im,~bg,C[f]['figH'],1); sheet.paste(t,(k*TW,20))
    D.text((k*TW+3,22),f'f{f:03d} ~{C[f]["yaw"]:.0f}deg',fill=(255,255,0))
    D.text((k*TW+3,34),f'bun dx {C[f]["bun_dx"]:+.2f} low {C[f]["hair_low"]:.3f}',fill=(255,255,0))
    if yaw in ours:
        v=ours[yaw]; b=Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA'); al=np.array(b)[...,3]>128
        g=Image.new('RGBA',b.size,(60,150,60,255)); g.alpha_composite(b)
        t=head_crop(g.convert('RGB'),al,O[v]['hair_parts']['figH'],1); sheet.paste(t,(k*TW,40+TH))
        m=O[v]['hair_parts']; D.text((k*TW+3,42+TH),f'OURS {v}',fill=(0,255,255)); D.text((k*TW+3,54+TH),f'bun dx {m["bun_dx"]:+.2f} low {m["hair_low"]:.3f}',fill=(0,255,255))
    else:
        D.text((k*TW+10,40+TH+TH//2),'no view (3/4 candidate)',fill=(150,150,150))
sheet.save(OUT+'/turn_sheet.png'); print(sheet.size)
