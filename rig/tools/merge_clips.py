#!/usr/bin/env python3
"""Merge the owners' key tracks for one action clip into a single clip (idle_clips.json schema), read-only on the owners' files.

usage: python3 rig/tools/merge_clips.py <clip> <out.json> [--skip=<owner>] [--stress]
  --stress: Body's source is body_tools/actions/stress/<clip>_stress.json (must carry stressTest: true); the merged clip keeps stressTest: true
  clip = jump | anger | run
Rules
  * each owner may only drive its own params (OWN below); a foreign track that holds 0 the whole time is dropped (logged),
    any other foreign track is an error
  * the same param driven by two owners = collision = error (exit 2), with one documented exception:
    BodyLean from Hair's hair_actions.json is dropped because Body folds Hair's lean offsets into body_tools/actions/*.json
    (parent/user instruction, 2026-09-30); Body's BodyLean is used
  * keys and viewKeys are merged per param; durations must agree within 1 frame (the longest is used, all tracks hold their last key)
"""
import json,sys,os,hashlib
ROOT='/workspace/shadowveil'
BODY=['BodyLean','ShoulderL','ShoulderR','ElbowL','ElbowR','HipL','HipR','KneeL','KneeR','AnkleL','AnkleR','ToeL','ToeR','RootX','RootY','HeadTilt','HeadNod']
OWN={'body':set(BODY),
     'hands':{f'Hand{s}{f}' for s in 'LR' for f in ('Thumb','Index','Middle','Ring','Pinky','Spread','ThumbSpread')}|{'WristL','WristR'},
     'mouth':{'MouthForm','MouthOpen'},
     'eyes':{'EyeBallX','EyeBallY','EyeLOpen','EyeROpen'},
     'hair':{'HairSwayX','HairSwayY'}}
SOURCES={ # owner -> (file, clip name inside the file or None for a single-clip file)
 'jump': [('body','body_tools/actions/jump.json',None),('hands','hands/actions/hand_actions.json','jump_hands'),('mouth','mouth/actions/mouth_actions.json','jump'),('eyes','eyes/showcase/eye_showcase.json','jump_eyes'),('hair','hair/actions/hair_actions.json','jump')],
 'anger':[('body','body_tools/actions/anger.json',None),('hands','hands/actions/hand_actions.json','anger_hands'),('mouth','mouth/actions/mouth_actions.json','anger'),('eyes','eyes/showcase/eye_showcase.json','anger_eyes'),('hair','hair/actions/hair_actions.json','anger')],
 'run':  [('body','body_tools/actions/run.json',None),('hands','hands/actions/hand_actions.json','run_hands'),('mouth','mouth/actions/mouth_actions.json','run'),('eyes','eyes/showcase/eye_showcase.json','run_eyes'),('hair','hair/actions/hair_actions.json','run')],
}
EXCEPT={('hair','BodyLean'):'dropped: Body folds Hair lean offsets into its own BodyLean (instruction 2026-09-30)'}
def load_clip(path,name):
    j=json.load(open(path))
    if name is None: return j if 'keys' in j else next(iter(j['clips'].values()))
    return j['clips'][name]
def zero(tr): return all(abs(v)<1e-9 for _,v in tr)
def merge(clip,skip=(),stress=False):
    rep={'clip':clip,'sources':[],'dropped':[],'missing':[],'errors':[]}
    owner_of={};src_of={};keys={};vkeys={};dur=[];loop=None;fps=30
    for owner,rel,name in SOURCES[clip]:
        if stress and owner=='body': rel=f'body_tools/actions/stress/{clip}_stress.json'
        if owner in skip: rep['dropped'].append(f'{owner}: whole source skipped');continue
        p=f'{ROOT}/{rel}'
        if not os.path.exists(p): rep['missing'].append(rel);continue
        try: c=load_clip(p,name)
        except Exception as e: rep['errors'].append(f'{rel}[{name}]: cannot load ({e})');continue
        rep['sources'].append(dict(owner=owner,file=rel,clip=name,sha256=hashlib.sha256(open(p,'rb').read()).hexdigest()[:16],duration=c.get('duration'),loop=c.get('loop')))
        dur.append(c.get('duration') or 0);fps=c.get('fps',fps)
        if owner=='body':
            loop=c.get('loop')
            if stress and c.get('stressTest') is not True: rep['errors'].append(f'{rel}: stress source without stressTest: true')
        tracks=[(None,k,t) for k,t in (c.get('keys') or {}).items()]+[(vw,k,t) for vw,d in (c.get('viewKeys') or {}).items() for k,t in d.items()]
        for vw,k,t in tracks:
            where=f'{owner}:{rel}:{vw or "keys"}:{k}'
            if (owner,k) in EXCEPT: rep['dropped'].append(f'{where} {EXCEPT[(owner,k)]}');continue
            if k not in OWN[owner]:
                if zero(t): rep['dropped'].append(f'{where} foreign param held at 0 (rest), dropped');continue
                rep['errors'].append(f'{where} drives a param owned by {[o for o in OWN if k in OWN[o]] or "nobody"}');continue
            src=f'{owner}:{rel}:{name}';prev=src_of.get(k)
            if prev and prev!=src: rep['errors'].append(f'COLLISION {k}: {prev} and {src}');continue
            src_of[k]=src;owner_of[k]=owner
            (keys if vw is None else vkeys.setdefault(vw,{}))[k]=t
    if dur and max(dur)-min(dur)>1.0/fps+1e-6: rep['errors'].append(f'durations disagree: {dur}')
    out={'fps':fps,'duration':max(dur) if dur else 0,'loop':bool(loop),'interp':'linear','keys':keys,'viewKeys':vkeys,'owners':owner_of}
    if stress: out['stressTest']=True
    return out,rep
if __name__=='__main__':
    clip,dst=sys.argv[1],sys.argv[2];skip=[a.split('=',1)[1] for a in sys.argv[3:] if a.startswith('--skip=')];stress='--stress' in sys.argv[3:]
    out,rep=merge(clip,skip,stress)
    for e in rep['errors']: print('ERROR',e,file=sys.stderr)
    if rep['errors']: sys.exit(2)
    json.dump({'format':'shadowveil merged action clip v1 (idle_clips.json schema), generated by rig/tools/merge_clips.py; do not edit','merge':rep,'clips':{clip:out}},open(dst,'w'),indent=0)
    print(json.dumps({k:rep[k] for k in ('missing','dropped')},indent=0)[:3000]);print('ok',clip,'duration',out['duration'],'loop',out['loop'],'params',sorted(out['owners']))
