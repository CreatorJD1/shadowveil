import json, csv, collections, sheet, os, glob
cls = json.load(open('classified.json'))
res = sheet.res
for c in cls:
    r = res[c['path']]
    c['green_side_count'] = ';'.join(str(len(f['green_side']['blobs'])) for f in r['faces'] if f.get('green_side'))
    c['amber_side_count'] = ';'.join(str(len(f['amber_side']['blobs'])) for f in r['faces'] if f.get('amber_side'))
ov = json.load(open('overrides.json'))
for c in cls:
    if c['path'] in ov:
        c.update(ov[c['path']]); c['confidence'] = 'eyeballed'
order = {'false':0,'uncertain':1,'true':2,'n/a':3}
cls.sort(key=lambda c: (c['source'] != 'art', order[c['consistent']], c['path']))
keys = ['path','source','category','angle','faces','mark_count','green_side_count','amber_side_count','positions','consistent','confidence','note','error']
with open('../all_stills.csv','w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
    for c in cls: w.writerow({k: c.get(k,'') for k in keys})
json.dump(cls, open('classified.json','w'))
for f in glob.glob('../sheets/*.jpg'): os.remove(f)
idx = []
for src in ('art', 'derived'):
    for verdict in ('false', 'uncertain'):
        sel = [c for c in cls if c['consistent'] == verdict and c['source'] == src]
        for i in range(0, len(sel), 40):
            fn = f'../sheets/{src}_{verdict}_{i//40+1:02d}.jpg'
            sheet.make(sel[i:i+40], fn, cols=8, W=300); idx.append((fn, [c['path'] for c in sel[i:i+40]]))
json.dump(idx, open('../sheets/index.json', 'w'), indent=0)
print(collections.Counter((c['source'], c['consistent']) for c in cls)); print(len(idx), 'sheets')
