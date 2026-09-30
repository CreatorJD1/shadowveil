import json, csv, collections
rows = [json.loads(l) for l in open('results.jsonl')]
cats = {r['path']: r for r in csv.DictReader(open('/tmp/all_stills.csv'))}
EXP = {'green': 2, 'amber': 1}
def conf_of(f):
    d = f['d']; c = 'high' if d >= 45 else 'medium' if d >= 28 else 'low'
    if f['mode'].startswith('single'):
        c = {'high': 'medium', 'medium': 'low', 'low': 'low'}[c]
    return c
out = []
for r in rows:
    faces = []
    for f in r.get('faces', []):
        sides = {}
        for s in ('green', 'amber'):
            cb = f.get(s + '_side')
            if cb is None: continue
            if cb.get('skin_frac', 1) < 0.5: continue
            sides[s] = [(round(b['x']), round(b['y'])) for b in cb['blobs']]
        if not sides: continue
        c = conf_of(f)
        ok = all(len(v) == EXP[s] for s, v in sides.items()) and not f.get('mirrored')
        faces.append(dict(mode=f['mode'], d=round(f['d']), conf=c, sides=sides, ok=ok, mirrored=f.get('mirrored', False)))
    if not faces:
        verdict, conf = 'n/a', ''
    else:
        good = [f for f in faces if f['conf'] != 'low']
        if not good: verdict, conf = 'uncertain', 'low'
        elif all(f['ok'] for f in good): verdict, conf = 'true', min((f['conf'] for f in good), key=['low','medium','high'].index)
        else: verdict, conf = 'false', max((f['conf'] for f in good if not f['ok']), key=['low','medium','high'].index)
    def fs(f):
        t = ' '.join(f"{'her-left(green)' if s=='green' else 'her-right(amber)'}={len(v)}@{';'.join(f'{x},{y}' for x,y in v) or '-'}" for s, v in f['sides'].items())
        return f"[{f['mode']} d={f['d']} {f['conf']}{' MIRRORED' if f['mirrored'] else ''}] {t}"
    c = cats.get(r['path'], {})
    p = r['path']
    derived = p.startswith(('/tmp/', '/home/')) or '/work/' in p or '/hairwork/' in p or '/qa/' in p or '/artifacts/' in p and '/imagine_' not in p and '/artifacts/turn/' not in p
    if derived and verdict in ('false', 'uncertain'): verdict_note = 'derived tool/QA output (not a regen target)'
    else: verdict_note = ''
    out.append(dict(path=r['path'], category=c.get('category', 'reference (own find)'), angle=c.get('angle', ''),
                    faces=len(faces), mark_count=';'.join(str(sum(len(v) for v in f['sides'].values())) for f in faces),
                    positions=' | '.join(fs(f) for f in faces), consistent=verdict, confidence=conf, source='derived' if derived else 'art', note=verdict_note, error=r.get('error', '')))
json.dump(out, open('classified.json', 'w'))
print(collections.Counter(o['consistent'] for o in out))
print(collections.Counter((o['consistent'], o['confidence']) for o in out))
