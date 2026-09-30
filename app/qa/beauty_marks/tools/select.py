import csv, re, collections
rows = list(csv.DictReader(open('/tmp/all_stills.csv')))
sel = []
skipre = re.compile(r'backup|/bak_|proto_tree|/old_|__pycache__|/\.vercel/|node_modules|/\.cache/|/layers/(stack|hierarchy)/|/rig/(?!apose\.json)')
for r in rows:
    p = r['path']
    if not p.startswith('/workspace/'): continue
    if skipre.search(p): continue
    try: w, h = int(r['width'] or 0), int(r['height'] or 0)
    except: continue
    if min(w, h) < 160: continue
    cat = r['category']
    if cat.startswith('part/layer'): continue
    if cat.startswith('duplicate'): continue
    inref = p.startswith('/workspace/shadowveil/reference/')
    if not inref:
        if r['cheek_visible'] not in ('yes', 'unknown'): continue
        if cat.startswith('video/render'): continue
    sel.append(r)
w = csv.DictWriter(open('selected.csv', 'w'), fieldnames=rows[0].keys()); w.writeheader(); w.writerows(sel)
print(len(sel)); print(collections.Counter(r['category'] for r in sel))
print(collections.Counter('/'.join(r['path'].split('/')[3:7]) for r in sel).most_common(30))
