import numpy as np, sys, json
from PIL import Image, ImageDraw
for clip in sys.argv[1:]:
    c=np.load(f'tmp/{clip}_crops.npy',mmap_mode='r'); r=[x for x in json.load(open(f'tmp/{clip}.json')) if x['ok']]
    idx=np.linspace(0,len(c)-1,16).astype(int)
    tiles=[]
    for i in idx:
        im=Image.fromarray(np.array(c[i])).resize((240,96)); d=ImageDraw.Draw(im)
        x=r[i]; d.text((2,2),f"{x['frame']} W{x['W']:.0f} oH{x['openH']:.1f} Hm{x['Hmouth']:.0f}",fill=(255,255,0))
        tiles.append(np.array(im))
    rows=[np.concatenate(tiles[k:k+4],1) for k in range(0,16,4)]
    Image.fromarray(np.concatenate(rows,0)).save(f'tmp/check_{clip}.png')
