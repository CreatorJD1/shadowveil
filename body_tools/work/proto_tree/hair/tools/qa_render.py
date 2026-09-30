import sys; from render import *
BOX={'apose':(530,20,820,370),'tpose':(530,20,830,360),'left':(540,20,845,330),'right':(515,20,830,330),'back':(545,20,820,345)}
def main():
  tag=sys.argv[1]; hd=sys.argv[2] if len(sys.argv)>2 else None
  vals=[(-1,0),(-.5,0),(0,0),(.5,0),(1,0),(0,-1),(0,1),(1,1),(-1,-1),(1,-1),(-1,1)]
  for v in ['apose','tpose','left','right','back']:
      h=hd.format(v) if hd else None
      ims=[Image.fromarray(render(v,sx,sy,BOX[v],hd=h,bg=(70,160,70))) for sx,sy in vals]
      w,hh=ims[0].size; s=Image.new('RGB',(w*len(ims),hh))
      for i,im in enumerate(ims): s.paste(im,(i*w,0))
      s.save(f'/workspace/shadowveil/hair/qa/{tag}_{v}.png')
      for (sx,sy),im in zip(vals,ims): im.save(f'/workspace/shadowveil/hair/qa/{tag}_{v}_{sx}_{sy}.png')
  print('done')

if __name__=='__main__': main()