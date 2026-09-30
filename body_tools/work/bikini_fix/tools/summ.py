import json,sys
for f in sys.argv[1:]:
    r=json.load(open(f)); print('==',f)
    cur=list(next(iter(r['poses'].values()))['curves'])
    print('pose     '+' '.join(f'{c[:12]:>26}' for c in cur))
    for nm,p in r['poses'].items():
        print(f'{nm:8} '+' '.join(f"{v['widthMed']:4.2f} d{v['dWidthP95VsRest'] or 0:4.2f}/{v['dWidthMaxVsRest'] or 0:4.2f} b{v['breaks']:2d} k{(v['newKinkInkDeg'] or 0):5.1f}" for v in p['curves'].values()))
