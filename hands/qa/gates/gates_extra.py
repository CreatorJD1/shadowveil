"""Hand parts qa_gates.py does not reach on its own (read-only; imports rig/qa_gates.py unchanged):
 (a) G2 leak on the staged F8 diagonals (hands/staged/f8_diagonals/<ang>/*.png), with qa_gates' own diagonal palette
     (all 5 base.png + her live hand files in all views + her turn frame for that angle) and its off_palette/chroma/soft counts.
 (b) G1-style weight bleed on the live rig/hand_angles meshes: weight > 0.001 on a bone that is not the vertex's dominant
     bone, its parent, child or sibling (same rule as qa_gates G1 bleed_vs_dominant_bone). F8/F5/F7/F10/F11 are rigid
     single-matrix PNG parts with no weights, so G1 does not apply to them."""
import sys,os,glob,json,importlib.util
os.environ['PYTHONDONTWRITEBYTECODE']='1'; sys.dont_write_bytecode=True
R='/workspace/shadowveil/'
spec=importlib.util.spec_from_file_location('qg',R+'rig/qa_gates.py'); qg=importlib.util.module_from_spec(spec); spec.loader.exec_module(qg)
out={'f8_leak':{},'hand_angles_weights':{}}; T=dict(off_palette=0,chroma=0,soft_edge=0,files=0)
for ang in ('45','135','225','315'):
    key='%03d'%int(ang)
    for f in sorted(glob.glob(R+f'hands/staged/f8_diagonals/{ang}/*.png')):
        r=qg.file_report(key,'hands',f,2.0); out['f8_leak'].setdefault(key,[]).append(r)
        T['files']+=1; T['off_palette']+=r['off_palette']; T['chroma']+=r['chroma']; T['soft_edge']+=r['soft_edge']
out['f8_leak_totals']=T; print('F8 leak totals',T)
for k,l in out['f8_leak'].items():
    bad=[(os.path.basename(r['file']),r['off_palette'],r['chroma']) for r in l if r['off_palette'] or r['chroma']]
    print(' ',k,len(l),'files; nonzero:',bad)
WT=dict(vertices=0,bleed_vertices=0)
for f in sorted(glob.glob(R+'rig/hand_angles/*_?.json')):
    d=json.load(open(f)); parts=d['parts']; idx={p['id']:i for i,p in enumerate(parts)}
    par={i:idx.get(p.get('parent')) for i,p in enumerate(parts)}
    def rel(a,b): return a==b or par.get(a)==b or par.get(b)==a or (par.get(a) is not None and par.get(a)==par.get(b))
    n=0;bad=0
    for w in d['weights']:
        n+=1; dom=max(w,key=lambda x:x[1])[0]
        if any(x[1]>1e-3 and not rel(int(x[0]),int(dom)) for x in w): bad+=1
    out['hand_angles_weights'][os.path.basename(f)]=dict(vertices=n,bleed_vertices=bad); WT['vertices']+=n; WT['bleed_vertices']+=bad
out['hand_angles_weights_totals']=WT; print('hand_angles weight bleed',WT, {k:v['bleed_vertices'] for k,v in out['hand_angles_weights'].items()})
json.dump(out,open(R+'hands/qa/gates/runs/extra.json','w'),indent=1)
