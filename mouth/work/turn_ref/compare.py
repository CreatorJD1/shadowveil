# Side-by-side: video frame vs our rest mouth, both scaled to the same CE (read-only on views/).
import json,csv; from PIL import Image,ImageDraw
rows={r['frame']:r for r in csv.DictReader(open('turn_mouth_frames.csv'))}; O=json.load(open('ours_rest.json'))
S=200; tiles=[]
def crop(im,cx,sy,ce,ey,cy,lab):
    x0,x1,y0,y1=cx-0.9*ce,cx+0.9*ce,sy-0.75*ce,sy+0.55*ce
    t=im.crop((int(x0),int(y0),int(x1),int(y1))).resize((int(1.8*S),int(1.3*S)),Image.LANCZOS)
    d=ImageDraw.Draw(t); k=S/ce
    for y,c in [(ey,(255,255,0)),(sy,(0,255,0)),(cy,(255,0,255))]:
        yy=(y-int(y0))*k; d.line([(0,yy),(8,yy)],fill=c,width=2); d.line([(t.width-8,yy),(t.width,yy)],fill=c,width=2)
    d.rectangle([0,0,t.width,14],fill=(0,0,0)); d.text((3,1),lab,fill=(255,255,255)); return t
pairs=[('f003','apose','front 0°'),('f060','left','left 90°'),('f159','right','right 270°')]
for f,v,n in pairs:
    r=rows[f]; im=Image.open(f'/workspace/shadowveil/reference/apose_turn/frames/{f}.png').convert('RGB')
    a=crop(im,float(r['mouthCx']),float(r['seamY']),58.26,176.74,235.0,f'video {f} {n} W={r["W_px"]}px')
    o=O[v]; b=Image.open(f'/workspace/shadowveil/views/{v}/base.png').convert('RGBA'); b.alpha_composite(Image.open(f'/workspace/shadowveil/views/{v}/mouth/rest.png').convert('RGBA'))
    bg=Image.new('RGBA',b.size,(0,0,255,255)); bg.alpha_composite(b)
    c=crop(bg.convert('RGB'),o['mouthCx'],o['seamY'],o['CE_px'],o['eyeLineY'],o['chinY'],f'ours {v} W={o["W_px"]}px ({o["W_px"]*58.26/o["CE_px"]:.1f} @videoCE)')
    tiles.append((a,c))
W=tiles[0][0].width; H=tiles[0][0].height
out=Image.new('RGB',(W*2+6,(H+4)*3+16),(40,40,40)); d=ImageDraw.Draw(out)
d.text((3,2),'same-CE scale; ticks: yellow=eye line, green=seam, magenta=chin',fill=(255,255,255))
for i,(a,c) in enumerate(tiles): out.paste(a,(0,16+i*(H+4))); out.paste(c,(W+6,16+i*(H+4)))
out.save('turn_vs_ours_rest.png')
