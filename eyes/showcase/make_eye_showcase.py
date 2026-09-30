# Eye showcase + eye tracks for the jump / anger / run test. Keys only; drives EyeLOpen/EyeROpen/EyeBallX/EyeBallY.
# Blink timing from Grok clips: close 42 ms, shut 250 ms, reopen 125 ms.
import json
def blink(t, both=True, eyes=('EyeLOpen','EyeROpen')):
    return {e:[[t,1],[t+0.042,0],[t+0.292,0],[t+0.417,1]] for e in eyes}
def merge(dst, src):
    for k,v in src.items(): dst.setdefault(k,[]).extend(v)
def clip(dur, keys, note, loop=False):
    for k in ('EyeLOpen','EyeROpen','EyeBallX','EyeBallY'):
        d = 1 if 'Open' in k else 0
        v = sorted(keys.get(k, []))
        if not v or v[0][0] > 0: v = [[0.0,d]] + v
        if v[-1][0] < dur: v = v + [[dur, v[-1][1] if loop else d]]
        keys[k] = [[round(t,3),round(x,3)] for t,x in v]
    return {"fps":30,"duration":dur,"loop":loop,"keys":keys,"note":note}
C = {}
# --- showcase 10.4 s ---
k = {}
merge(k, blink(0.6))
for e in ('EyeLOpen','EyeROpen'):   # slow lid sweep through all 8 lid frames and back
    k[e] += [[1.4,1],[2.8,0],[3.1,0],[4.5,1]]
k['EyeBallX'] = [[4.8,0],[5.0,-1],[5.5,-1],[5.8,1],[6.3,1],[6.5,0]]
k['EyeBallY'] = [[6.6,0],[6.8,-1],[7.2,-1],[7.5,1],[7.9,1],[8.1,0]]
merge(k, blink(8.4, eyes=('EyeROpen',)))   # her right (amber) alone: checks each lid is independent
merge(k, blink(9.2, eyes=('EyeLOpen',)))   # her left (green) alone
C['eye_showcase'] = clip(10.4, k, "rest, blink at real timing, slow lid sweep f0-f7, gaze to each limit, each eye blinks alone, rest")
# --- anger 3.0 s: narrowed upper lid (frame 2), fixed level stare, one blink going in, none during the glare ---
k = {}
for e in ('EyeLOpen','EyeROpen'): k[e] = [[0.05,1],[0.092,0],[0.342,0],[0.467,0.72],[2.6,0.72],[2.9,1]]
k['EyeBallY'] = [[0.3,0],[0.45,-0.1],[2.6,-0.1],[2.9,0]]
C['anger_eyes'] = clip(3.0, k, "no brows exist, so eyes can only narrow the upper lid (frame 2 of 7) and hold a fixed stare; retime to Body's pose beats")
# --- jump 1.6 s: look down on crouch, eyes lead up ~3 frames before takeoff, blink on landing impact ---
k = {}
k['EyeBallY'] = [[0.05,0],[0.25,0.5],[0.38,0.5],[0.42,-0.6],[0.85,-0.6],[1.0,0.3],[1.35,0.3],[1.55,0]]
merge(k, blink(1.058))   # shut lands on the impact frame; retime t to Body's landing
C['jump_eyes'] = clip(1.6, k, "crouch 0.25-0.45 looks down, gaze leads takeoff by ~3 frames, blink closes on landing (1.05 s); shift to Body's beats")
# --- run 2.0 s loop: steady forward gaze, tiny vertical bob with the stride, one blink per loop ---
k = {}
k['EyeBallY'] = [[round(i/6,3), 0.2 if i%2==0 else 0.1] for i in range(13)]
merge(k, blink(1.4))
C['run_eyes'] = clip(2.0, k, "forward gaze with a small stride bob, one blink per 2 s loop; set the bob period to Body's stride", loop=True)
json.dump({"format":"shadowveil idle clips v1 (same schema as body_tools/idle/idle_clips.json)",
           "spec":"value(t)=linear interpolation; EyeOpen frame=round((1-v)*7); EyeBallY -1 up, +1 down; params not listed stay default",
           "generator":"python3 eyes/showcase/make_eye_showcase.py","clips":C}, open('eye_showcase.json','w'), indent=1)
# validate
for n,c in C.items():
    for p,v in c['keys'].items():
        ts=[a for a,_ in v]; assert ts==sorted(ts),(n,p)
        for _,x in v: assert (0<=x<=1) if 'Open' in p else (-1<=x<=1),(n,p,x)
    print(n, c['duration'], {p:(c['keys'][p][0][1],c['keys'][p][-1][1]) for p in c['keys']})
