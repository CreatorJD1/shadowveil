# MediaPipe pose landmarks on the benchmark images (read-only; only landmark numbers are kept).
import sys, json, math, mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
A='/home/box/agent-data/agents/206a2578-0898-4eea-b85a-d95ac9bd9da0/attachments/'
ids=["ab144dd433c54f34d5cb8438cf38bf70e1c2ce7bf3b91f8891c36357b1272dfc","12901b7ca3021e69921d261e9279c581d145f54f855a6065c25c01066adbdeea","b0810c3d09f6a3992e66f2c4f526b3bbf6c57ede872877fe06157478ba13dfca","3b58b0c3df59994781ce43eb8152b4afb5195a68e74e40f58b043626de14ea6b","546a9d80a001d7f2c9d50d6312fab8cb198b6cfb6514310fb726d0a648b37458","1ef68fbe4d8401fbc0646ce21ff5532bb85436d09d1d964b220f8aff0f55b4f4"]
names=['nose','leye_in','leye','leye_out','reye_in','reye','reye_out','lear','rear','mouth_l','mouth_r','lsho','rsho','lelb','relb','lwri','rwri','lpinky','rpinky','lindex','rindex','lthumb','rthumb','lhip','rhip','lknee','rknee','lank','rank','lheel','rheel','lfoot','rfoot']
det=vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path='/tmp/pose_heavy.task'),running_mode=vision.RunningMode.IMAGE))
out={}
for i,x in enumerate(ids,1):
    img=mp.Image.create_from_file(A+x+'.jpg'); r=det.detect(img)
    if not r.pose_landmarks: out[i]=None; continue
    L=r.pose_landmarks[0]; W,H=img.width,img.height
    out[i]={n:[round(l.x*W,1),round(l.y*H,1),round(l.z*W,1),round(l.visibility,2)] for n,l in zip(names,L)}
json.dump(out,open(sys.argv[1],'w'),indent=0)
