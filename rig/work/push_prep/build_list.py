import os, re, json, fnmatch, subprocess
R = '/workspace/shadowveil'; OUT = f'{R}/rig/work/push_prep'
MAX = 50 * 1024 * 1024
SECRET = re.compile(r'(^|/)(remote/|\.env($|\.)|.*token.*|.*secret.*|.*\.pem$|.*\.key$|.*\.crt$|.*\.p12$|.*\.pfx$|id_rsa.*|.*credential.*)', re.I)
BAD = [(re.compile(r'(^|/)backup[_s]?[^/]*(/|$)', re.I), 'backup'), (re.compile(r'\.tmp$'), '*.tmp'), (re.compile(r'(^|/)__pycache__(/|$)|\.pyc$'), 'pycache'),
       (re.compile(r'(^|/)(frames_[^/]*|frame_dump[^/]*|frames)/'), 'frame dump'), (re.compile(r'(^|/)(renders?|scratch)/'), 'scratch render')]
inc = {}; exc = []
def consider(p, owner, root=None, scratch_rules=True):
    full = f'{R}/{p}'
    if not os.path.isfile(full): exc.append((p, owner, 'missing')); return
    if root and not p.startswith(root): exc.append((p, owner, f'not under {root}')); return
    if SECRET.search(p): exc.append((p, owner, 'secret-looking name')); return
    if scratch_rules:
        for rx, why in BAD:
            if rx.search(p): exc.append((p, owner, why)); return
    if os.path.getsize(full) > MAX: exc.append((p, owner, '>50 MB')); return
    inc[p] = owner
for m, owner, root in (('body_tools/work/push_manifest.txt', 'Base Body', 'body_tools/'), ('hands/push_manifest.txt', 'Base Hands', 'hands/'),
                       ('hair/push_manifest.txt', 'Base Hair', 'hair/'), ('mouth/push_manifest.txt', 'Mouth', 'mouth/')):
    for l in open(f'{R}/{m}'):
        l = l.strip()
        if l and not l.startswith('#'): consider(l, owner, root, scratch_rules=False)   # owners' manifests are taken as listed (checked: exists, under owner, size, secrets)
    consider(m, owner, root, scratch_rules=False)
# coder share
co = ['rig/index.html', 'rig/poser.html', 'rig/qa_gates.py', 'rig/partmesh/staged/headgroup.json', 'rig/partmesh/staged/armsub.json']
for d in ('rig/poser', 'rig/benchmarks', 'status'):
    for dp, dn, fn in os.walk(f'{R}/{d}'):
        for f in fn: co.append(os.path.relpath(f'{dp}/{f}', R))
SMALL = 1024 * 1024
for d in ('qa_gates', 'crotch_weights', 'armsub', 'handorder', 'irislimits', 'hgsubhair', 'hairless'):
    for dp, dn, fn in os.walk(f'{R}/rig/work/{d}'):
        for f in fn:
            p = os.path.relpath(f'{dp}/{f}', R); ext = os.path.splitext(f)[1].lower()
            if ext in ('.md', '.py', '.js', '.mjs', '.sh', '.json'):
                if ext == '.json' and os.path.getsize(f'{R}/{p}') > SMALL: exc.append((p, 'Coder', 'large json (>1 MB: candidate skins / render dumps, regenerable)')); continue
                co.append(p)
            elif ext == '.png' and os.path.getsize(f'{R}/{p}') <= 1024 * 1024 and re.search(r'sheet|cmp|contact|grid|notch|handoff_arms', f): co.append(p)
            elif ext == '.png': exc.append((p, 'Coder', 'scratch render (full-frame / per-pose render, not a sheet)'))
            else: exc.append((p, 'Coder', 'not README/script/json/small sheet' + (' (html copy of index)' if ext == '.html' else '')))
for p in co: consider(p, 'Coder')
# eyes changes since 3515d57 (modified + untracked, computed with a temp index read from 3515d57)
env = dict(os.environ, GIT_INDEX_FILE=f'{OUT}/index.tmpidx'); G = ['git', '--git-dir=/workspace/.shadowveil-git', f'--work-tree={R}']
subprocess.run(G + ['read-tree', '3515d57'], env=env, check=True, cwd=R)
ch = subprocess.run(G + ['diff', '--name-only', '--', 'eyes/'], env=env, capture_output=True, text=True, cwd=R).stdout.split()
ch += subprocess.run(G + ['ls-files', '--others', '--exclude-standard', '--', 'eyes/'], env=env, capture_output=True, text=True, cwd=R).stdout.split()
for p in ch: consider(p, 'Base Eyes', 'eyes/')
json.dump({'include': inc, 'exclude': exc}, open(f'{OUT}/list.json', 'w'), indent=1)
from collections import Counter
print(Counter(inc.values())); print(Counter((o, w) for _, o, w in exc))
