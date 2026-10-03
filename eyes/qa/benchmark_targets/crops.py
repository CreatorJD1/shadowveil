"""Fixed-zoom eye/brow crops of the six benchmarks (target reference only; never used as paint)."""
from PIL import Image
A='/home/box/agent-data/agents/206a2578-0898-4eea-b85a-d95ac9bd9da0/attachments/'
B=[('1_laugh','ab144dd433c54f34d5cb8438cf38bf70e1c2ce7bf3b91f8891c36357b1272dfc',(556,278)),
   ('2_sideeye','12901b7ca3021e69921d261e9279c581d145f54f855a6065c25c01066adbdeea',(596,280)),
   ('3_smirk','b0810c3d09f6a3992e66f2c4f526b3bbf6c57ede872877fe06157478ba13dfca',(568,276)),
   ('4_cheer','3b58b0c3df59994781ce43eb8152b4afb5195a68e74e40f58b043626de14ea6b',(545,366)),
   ('5_angry','546a9d80a001d7f2c9d50d6312fab8cb198b6cfb6514310fb726d0a648b37458',(556,290)),
   ('6_sad','1ef68fbe4d8401fbc0646ce21ff5532bb85436d09d1d964b220f8aff0f55b4f4',(598,322))]
W,H,Z=200,110,2   # fixed source window (px) and zoom for all six
def crop(i):
    n,f,(cx,cy)=B[i]; im=Image.open(A+f+'.jpg').convert('RGB')
    box=(cx-W//2,cy-H//2-12,cx+W//2,cy+H//2-12)
    return im.crop(box).resize((W*Z,H*Z),Image.LANCZOS),box
if __name__=='__main__':
    S=Image.new('RGB',(W*Z*2,H*Z*3),'white')
    for i in range(6): c,_=crop(i); S.paste(c,((i%2)*W*Z,(i//2)*H*Z))
    S.save('/workspace/tmp_bt/crops.png')
