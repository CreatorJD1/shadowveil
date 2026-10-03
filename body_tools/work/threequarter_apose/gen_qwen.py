import sys, base64, json, io, time
from gradio_client import Client
from PIL import Image
src, prompt, out = sys.argv[1], sys.argv[2], sys.argv[3]
lora = sys.argv[4] if len(sys.argv)>4 else "Multiple-Angles"
seed = int(sys.argv[5]) if len(sys.argv)>5 else 0
b64 = "data:image/png;base64,"+base64.b64encode(open(src,'rb').read()).decode()
c = Client("prithivMLmods/Qwen-Image-Edit-2509-LoRAs-Fast", verbose=False)
t=time.time()
r = c.predict(b64, prompt, lora, seed, seed==0, 1.0, 4, api_name="/edit_image")
d = r["image"].split(",",1)[1]
im = Image.open(io.BytesIO(base64.b64decode(d))); im.save(out)
json.dump({"src":src,"prompt":prompt,"lora":lora,"seed":r.get("seed"),"size":im.size,"secs":time.time()-t,"space":"prithivMLmods/Qwen-Image-Edit-2509-LoRAs-Fast"}, open(out+".json","w"))
print(out, im.size, r.get("seed"))
