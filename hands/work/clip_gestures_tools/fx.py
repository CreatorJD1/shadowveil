import subprocess,numpy as np,os,sys
VD='/workspace/shadowveil/reference/grok_build/public/clean-room/videos'
def load(clip):
    p=f'/workspace/gb/npy/{clip}.npy'
    if os.path.exists(p): return np.load(p,mmap_mode='r')
    w,h=[int(x) for x in subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','csv=p=0',f'{VD}/{clip}.mp4']).decode().strip().split(',')]
    raw=subprocess.run(['ffmpeg','-v','error','-i',f'{VD}/{clip}.mp4','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    F=np.frombuffer(raw,np.uint8).reshape(-1,h,w,3); os.makedirs('/workspace/gb/npy',exist_ok=True); np.save(p,F); return F
