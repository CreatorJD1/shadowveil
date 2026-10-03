import os, re, json, subprocess
R='/workspace/shadowveil'; OUT=f'{R}/rig/work/push_prep'; MAX=50*1024*1024; SMALL=1024*1024
SECRET=re.compile(r'(^|/)(remote/|\.env($|\.)|.*token.*|.*secret.*|.*\.pem$|.*\.key$|.*\.crt$|.*\.p12$|.*\.pfx$|id_rsa.*|.*credential.*)',re.I)
inc={}; exc=[]
def consider(p,owner,root=None):
    full=f'{R}/{p}'
    if not os.path.isfile(full): exc.append((p,owner,'missing')); return
    if root and not p.startswith(root): exc.append((p,owner,f'not under {root}')); return
    if SECRET.search(p): exc.append((p,owner,'secret-looking name')); return
    if os.path.getsize(full)>MAX: exc.append((p,owner,'>50 MB')); return
    inc[p]=owner
for m,owner,root in (('eyes/push_manifest.txt','Eyes','eyes/'),('body_tools/work/push_manifest.txt','Body','body_tools/'),('hands/push_manifest.txt','Hands','hands/'),('hair/push_manifest.txt','Hair','hair/'),('mouth/push_manifest.txt','Mouth','mouth/')):
    for l in open(f'{R}/{m}'):
        l=l.strip()
        if l and not l.startswith('#'): consider(l,owner,root)
    consider(m,owner,root)
for h in ('eyes/HANDOFF_EYES.md','body_tools/work/HANDOFF_BODY.md','hands/HANDOFF_HANDS.md','hair/HANDOFF_HAIR.md','mouth/HANDOFF_MOUTH.md'):
    if h not in inc: print('handoff not in manifest, adding:',h); consider(h,'handoff')
# Coder
env=dict(os.environ,GIT_INDEX_FILE=f'{OUT}/index2.tmpidx'); G=['git','--git-dir=/workspace/.shadowveil-git',f'--work-tree={R}']
subprocess.run(G+['read-tree','a803a02'],env=env,check=True,cwd=R)
mod=subprocess.run(G+['diff','--name-only','--','rig','status','app'],env=env,capture_output=True,text=True,cwd=R).stdout.split('\n')
unt=subprocess.run(G+['ls-files','--others','--exclude-standard','--','rig','status','app'],env=env,capture_output=True,text=True,cwd=R).stdout.split('\n')
ign=subprocess.run(G+['ls-files','--others','--ignored','--exclude-standard','--','rig/work','rig/poser','rig/partmesh','status','app'],env=env,capture_output=True,text=True,cwd=R).stdout.split('\n')
CODE=('.md','.py','.js','.mjs','.sh','.json','.txt','.css','.diff')
for p in sorted(set(x for x in mod+unt+ign if x)):
    f=os.path.basename(p); ext=os.path.splitext(f)[1].lower(); sz=os.path.getsize(f'{R}/{p}') if os.path.isfile(f'{R}/{p}') else 0
    why=None
    if '__pycache__' in p or ext=='.pyc': why='pycache'
    elif re.search(r'\.bak|backup',p,re.I): why='backup'
    elif p.startswith('rig/work/push_prep/') and not f in ('build_list.py','build_list2.py','COMMIT_MSG.txt','COMMIT_MSG2.txt'): why='push scratch'
    elif p.startswith('rig/previews/'):
        if p in mod and ext!='.log': pass
        else: why='render scratch (rig/previews renders/logs)'
    elif p.startswith('rig/') and p.count('/')==1:
        if f not in ('index.html','poser.html','qa_gates.py','rest_check.py'): why='rig top-level working copy/test page/render'
    elif p.startswith('rig/work/'):
        if re.search(r'/(renders?|out|tmp|frames[^/]*|scratch)/',p): why='scratch render dir'
        elif ext=='.log' or ext=='.err' or ext=='.out': why='log'
        elif ext in CODE:
            if ext in ('.json','.txt') and sz>SMALL: why='large json/txt (>1 MB, regenerable)'
        elif ext=='.html':
            if sz>SMALL: why='large html'
        elif ext=='.png':
            if sz>SMALL or not re.search(r'sheet|cmp|contact|grid|notch|before_after|compare',f): why='scratch render png'
        else: why=f'binary/scratch ({ext or "noext"})'
    if why: exc.append((p,'Coder',why))
    else: consider(p,'Coder')
consider('rig/work/crotch_weights/apose_skin_ulnb.json','Coder')
exc[:]=[e for e in exc if e[0]!='rig/work/crotch_weights/apose_skin_ulnb.json']
for p in ('STATUS.md','HANDOFF.md','AGENTS.md'): consider(p,'Root')
json.dump({'include':inc,'exclude':exc},open(f'{OUT}/list2.json','w'),indent=1)
open(f'{OUT}/paths2.txt','w').write('\n'.join(sorted(inc))+'\n')
from collections import Counter
sz=Counter()
for p,o in inc.items(): sz[o]+=os.path.getsize(f'{R}/{p}')
for o,n in Counter(inc.values()).items(): print(o,n,round(sz[o]/1e6,1),'MB')
print('total',len(inc),round(sum(sz.values())/1e6,1),'MB')
print(Counter((o,w) for _,o,w in exc))
