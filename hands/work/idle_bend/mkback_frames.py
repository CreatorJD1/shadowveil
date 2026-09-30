# mkback_frames.py <name> <pattern e.g. 01112>  : finger (Index..Pinky, seg1-3) frame list re-indexed from the live 3 entries
import json,sys,os
n,pat=sys.argv[1],sys.argv[2];j=json.load(open('data_backup/back_rig.json'))
for p in j['parts']:
    if any(f in p['id'] for f in ['Index','Middle','Ring','Pinky']) and p.get('frames'):
        fr=p['frames'];assert len(fr)==3;p['frames']=[fr[int(c)] for c in pat]
os.makedirs(f'scratch/back_{n}',exist_ok=True);json.dump(j,open(f'scratch/back_{n}/rig.json','w'),indent=1)
