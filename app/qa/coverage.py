#!/usr/bin/env python3
"""Map every Clean room media file (public/clean-room/** + artifacts/**) to where the app uses it."""
import json, pathlib, csv, collections, re
ROOT = pathlib.Path('/workspace/shadowveil'); GB = ROOT / 'reference/grok_build'
gal = json.loads((ROOT / 'app/cleanroom/gallery.json').read_text())
cr = (ROOT / 'app/cleanroom/index.html').read_text()
rig = json.loads((GB / 'public/clean-room/rig/apose.json').read_text())
rigsrc = set(re.findall(r'/clean-room/([^"\']+)', json.dumps(rig)))
drv = (ROOT / 'app/driver/poses.json').read_text()
reg = (ROOT / 'app/registry.json').read_text()
rows = []
for g in gal['groups']:
    for it in g['items']:
        p = it['p']; uses = [f"gallery:{g['id']}"]
        rel = p.replace('public/clean-room/', '')
        if 'public/clean-room/' in p and ('clean-room/' + rel in cr or rel in rigsrc): uses.append('cleanroom-page')
        if p in drv: uses.append('driver')
        if 'reference/grok_build/' + p in reg: uses.append('registry')
        rows.append(dict(path='reference/grok_build/' + p, kind=it['k'], group=g['id'], used_in=' + '.join(uses)))
with open(ROOT / 'app/qa/cleanroom_coverage.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['path', 'kind', 'group', 'used_in']); w.writeheader(); w.writerows(rows)
media = [r for r in rows if r['kind'] in ('image', 'video')]
used = [r for r in media if r['used_in']]
c = collections.Counter(r['group'] for r in rows)
L = ['# Clean room coverage (media file -> where it is used in the app)', '',
     f'Media files (png/jpg/mp4): {len(media)}; used: {len(used)} ({100*len(used)/len(media):.1f}%). All files incl. json/html/md/zip: {len(rows)}, all listed in the gallery.', '',
     'Where: gallery:<group> = app/cleanroom/gallery.html?g=<group> (#reference tab "Clean room media gallery"); cleanroom-page = patched app/cleanroom/index.html; driver = app/driver (poses.json); registry = app/registry.json media entry.', '',
     '| group | files | also in Clean room page | also in driver |', '|---|---|---|---|']
for g in gal['groups']:
    rs = [r for r in rows if r['group'] == g['id']]
    L.append(f"| {g['title']} | {len(rs)} | {sum('cleanroom-page' in r['used_in'] for r in rs)} | {sum('driver' in r['used_in'] for r in rs)} |")
L += ['', 'Driver uses:', ''] + [f"- {r['path']} ({r['used_in']})" for r in rows if 'driver' in r['used_in']]
L += ['', 'Full per-file list: app/qa/cleanroom_coverage.csv']
(ROOT / 'app/qa/cleanroom_coverage.md').write_text('\n'.join(L))
print(L[2]); print(sum('driver' in r['used_in'] for r in rows), 'driver', sum('cleanroom-page' in r['used_in'] for r in rows), 'page')
