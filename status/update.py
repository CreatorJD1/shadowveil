#!/usr/bin/env python3
"""Shadowveil status helper. Edits only status/status.json and STATUS.md.

  update.py touch                      set 'last updated' to now (PT)
  update.py move 'item text' STATE     set state of the first item/sub-item whose text contains
                                       'item text' (case-insensitive). STATE: done|wip|todo|blocked|decision
                                       Top-level items are also moved to that state's section
                                       (done->built, wip->progress, blocked/decision->blockers, todo->next).
                                       Add --stay to keep it in its current section.
  update.py add SECTION 'text' [STATE] add an item to a section (built|progress|blockers|next)
  update.py progress 50 ['label']      set overall percent (and optional label)
  update.py owner Body 'latest item'   set an owner's latest item
  update.py scan                       rescan video globs + check output links exist
  update.py md                         regenerate STATUS.md only
  update.py build TAB 'text'           set the build status line shown on a tab (status|preview|body|...)
  update.py register SECTION KIND PATH 'label' ['note']
                                       register a tool page / report / media in app/registry.json
                                       SECTION: body|eyes|mouth|hands|hair|coder|reference
                                       KIND: pages|reports|media   (PATH relative to /workspace/shadowveil)
  update.py check [BASE_URL]           HTTP-check every path in status.json + registry.json
                                       (default http://127.0.0.1:8765/), print broken ones
'scan' also rescans app/registry.json: every section's scan_dirs for new .html / .mp4 / .md /
SUMMARY|REPORT .txt files and top-level .png, adds them as auto entries, drops auto entries whose
file vanished, flags missing ones (exists:false, hidden by the app), and rebuilds the HTML inventory.
Every command (except md) also touches the timestamp and regenerates STATUS.md.
"""
import sys, json, glob, os, subprocess, datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # /workspace/shadowveil
JSON = os.path.join(HERE, 'status.json')
MD = os.path.join(ROOT, 'STATUS.md')
REG = os.path.join(ROOT, 'app', 'registry.json')
PT = ZoneInfo('America/Los_Angeles')
STATES = ['done', 'wip', 'todo', 'blocked', 'decision']
STATE_SECTION = {'done': 'built', 'wip': 'progress', 'blocked': 'blockers', 'decision': 'blockers', 'todo': 'next'}

def load():
    with open(JSON) as f: return json.load(f)

def save(d):
    tmp = JSON + '.tmp'
    with open(tmp, 'w') as f: json.dump(d, f, indent=2, ensure_ascii=False); f.write('\n')
    os.replace(tmp, JSON)

def touch(d):
    now = datetime.datetime.now(PT)
    d['updated'] = now.isoformat(timespec='seconds')
    d['updated_pt'] = now.strftime('%a %b %-d %Y, %-I:%M %p PT')

def section(d, sid):
    for s in d['sections']:
        if s['id'] == sid: return s
    sys.exit(f'no section {sid!r}; have ' + ', '.join(s['id'] for s in d['sections']))

def find(d, text):
    t = text.lower()
    for s in d['sections']:
        for it in s['items']:
            if t in it['text'].lower(): return s, it, None
            for sub in it.get('sub', []):
                if t in sub['text'].lower(): return s, sub, it
    sys.exit(f'no item matching {text!r}')

def probe(path):
    try:
        out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=width,height',
                              '-of', 'json', path], capture_output=True, text=True, timeout=20).stdout
        j = json.loads(out); st = (j.get('streams') or [{}])[0]
        return round(float(j['format']['duration']), 1), st.get('width'), st.get('height')
    except Exception:
        return None, None, None

def scan(d):
    seen, vids = set(), []
    old = {v['path']: v for v in d.get('videos', [])}
    for src in d.get('video_sources', []):
        for p in sorted(glob.glob(os.path.join(ROOT, src['glob']), recursive=True)):
            rel = os.path.relpath(p, ROOT)
            if rel in seen or not os.path.isfile(p): continue
            seen.add(rel)
            mt = datetime.datetime.fromtimestamp(os.path.getmtime(p), PT)
            dur, w, h = probe(p)
            v = {'path': rel, 'group': src['group'], 'version': src['version'],
                 'name': os.path.splitext(os.path.basename(p))[0],
                 'date': mt.strftime('%b %-d %-I:%M %p PT'), 'mtime': mt.isoformat(timespec='seconds'),
                 'duration': dur, 'size': [w, h], 'bytes': os.path.getsize(p)}
            if rel not in old: print('new video:', rel)
            vids.append(v)
    gone = set(old) - seen
    for g in gone: print('removed (missing):', g)
    d['videos'] = vids
    for o in d.get('outputs', []):
        o['exists'] = os.path.exists(os.path.join(ROOT, o['path']))
        if not o['exists']: print('missing output (hidden):', o['path'])
    print(f"{len(vids)} videos, {sum(o['exists'] for o in d.get('outputs', []))}/{len(d.get('outputs', []))} outputs exist")

MARK = {'done': '[x]', 'wip': '[~]', 'todo': '[ ]', 'blocked': '[!]', 'decision': '[?]'}

def md(d):
    L = [f"# {d['title']}", '', f"Last updated: {d['updated_pt']}", '',
         f"Overall: ~{d['progress']['pct']}% — {d['progress']['label']} ({d['progress']['note']})", '',
         'Legend: [x] done  [~] in progress  [ ] to do  [!] blocked  [?] needs USER DECISION', '',
         'Dashboard: http://127.0.0.1:8765/app/#status (master app; /status/ redirects there). Data: status/status.json, app/registry.json', '']
    for s in d['sections']:
        L += [f"## {s['title']}", '']
        if s.get('intro'): L += [s['intro'], '']
        for it in s['items']:
            tag = ' **USER DECISION**' if it.get('state') == 'decision' else ''
            L.append(f"- {MARK.get(it.get('state'), '[ ]')}{tag} {it['text']}")
            for sub in it.get('sub', []):
                L.append(f"    - {MARK.get(sub.get('state'), '[ ]')} {sub['text']}")
        L.append('')
    if d.get('build_lines'):
        L += ['## Build status per tab', ''] + [f'- {k}: {v}' for k, v in d['build_lines'].items()] + ['']
    L += ['## Owners', '']
    for o in d['owners']: L.append(f"- **{o['name']}** ({o.get('state', '')}): {o['latest']}")
    L += ['', '## Latest outputs', '']
    for o in d['outputs']:
        if o.get('exists'): L.append(f"- {o['label']}: {o['path']}")
    L += ['', '## Rendered clips', '']
    for v in d.get('videos', []):
        L.append(f"- [{v['version']}] {v['path']} ({v['date']}, {v['duration']} s)")
    L += ['', '## Live rig', '', d['live_rig']['note'], '']
    with open(MD, 'w') as f: f.write('\n'.join(L))


import re, urllib.request, urllib.parse
KIND_OF = {'.html': 'pages', '.mp4': 'media', '.webm': 'media', '.png': 'media', '.gif': 'media',
           '.md': 'reports', '.txt': 'reports', '.json': 'reports', '.log': 'reports'}

def load_reg():
    with open(REG) as f: return json.load(f)

def save_reg(r):
    tmp = REG + '.tmp'
    with open(tmp, 'w') as f: json.dump(r, f, indent=2, ensure_ascii=False); f.write('\n')
    os.replace(tmp, REG)

def html_title(p):
    try:
        with open(p, 'rb') as f: head = f.read(20000).decode('utf-8', 'ignore')
        m = re.search(r'<title>([^<]*)', head, re.I); return m.group(1).strip() if m else ''
    except Exception: return ''

def pretty(rel):
    b = os.path.splitext(os.path.basename(rel))[0]
    if b == 'index': b = os.path.basename(os.path.dirname(rel)) or b
    return b.replace('_', ' ')

def scan_reg():
    r = load_reg(); ex = r.get('scan_exclude', [])
    skip = lambda rel: any(e in rel for e in ex)
    for sec in r['sections']:
        known = {e['path'] for k in ('pages', 'reports', 'media') for e in sec[k]}
        for d in sec.get('scan_dirs', []):
            base = os.path.join(ROOT, d)
            for dp, dns, fns in os.walk(base):
                reld = os.path.relpath(dp, ROOT)
                if skip(reld + '/'): dns[:] = []; continue
                depth = reld.count('/') - d.count('/')
                for fn in fns:
                    rel = os.path.join(reld, fn); ext_ = os.path.splitext(fn)[1].lower()
                    if rel in known or skip(rel) or ext_ not in KIND_OF: continue
                    if ext_ in ('.png', '.gif') and depth > 0: continue          # only top-level images
                    if ext_ in ('.txt', '.log', '.json') and not re.match(r'(SUMMARY|REPORT)', fn, re.I): continue
                    if sec['id'] == 'coder' and ext_ == '.mp4': continue       # clips live in status.json gallery
                    kind = KIND_OF[ext_]
                    e = {'label': html_title(os.path.join(ROOT, rel)) or pretty(rel) if kind == 'pages' else pretty(rel),
                         'path': rel, 'note': 'auto-registered by update.py scan', 'auto': True}
                    sec[kind].append(e); known.add(rel); print(f'registered [{sec["id"]}/{kind}]', rel)
        for k in ('pages', 'reports', 'media'):
            keep = []
            for e in sec[k]:
                e['exists'] = os.path.exists(os.path.join(ROOT, e['path']))
                if not e['exists'] and e.get('auto'): print('dropped (gone):', e['path']); continue
                if not e['exists']: print('missing (hidden):', e['path'])
                keep.append(e)
            sec[k] = keep
    # inventory of every html page
    where = {e['path']: s['id'] for s in r['sections'] for e in s['pages']}
    inv = []
    for dp, dns, fns in os.walk(ROOT):
        if 'node_modules' in dp or '/.' in dp: dns[:] = []; continue
        for fn in fns:
            if not fn.endswith('.html'): continue
            rel = os.path.relpath(os.path.join(dp, fn), ROOT)
            if rel.startswith(('app/', 'status/')): continue
            inv.append({'path': rel, 'title': html_title(os.path.join(dp, fn)), 'bytes': os.path.getsize(os.path.join(dp, fn)),
                        'embedded_in': where.get(rel, ''), 'excluded': skip(rel)})
    r['inventory'] = sorted(inv, key=lambda x: x['path'])
    save_reg(r)
    print(f"registry: {sum(len(s[k]) for s in r['sections'] for k in ('pages','reports','media'))} entries, {len(inv)} html pages inventoried")

def register(a):
    if len(a) < 5 or a[2] not in ('pages', 'reports', 'media'): sys.exit('usage: register SECTION pages|reports|media PATH LABEL [NOTE]')
    r = load_reg(); sec = next((s for s in r['sections'] if s['id'] == a[1]), None)
    if not sec: sys.exit('unknown section; have ' + ', '.join(s['id'] for s in r['sections']))
    rel = os.path.relpath(os.path.abspath(os.path.join(ROOT, a[3])), ROOT) if not os.path.isabs(a[3]) else os.path.relpath(a[3], ROOT)
    if not os.path.exists(os.path.join(ROOT, rel)): sys.exit(f'{rel} does not exist')
    sec[a[2]] = [e for e in sec[a[2]] if e['path'] != rel]
    sec[a[2]].append({'label': a[4], 'path': rel, 'note': a[5] if len(a) > 5 else '', 'exists': True})
    save_reg(r); print('registered', rel, 'in', a[1], a[2])

def check(base):
    d = load(); r = load_reg()
    paths = ['app/', 'app/index.html', 'app/registry.json', 'status/', 'status/status.json', 'STATUS.md']
    paths += [v['path'] for v in d.get('videos', [])] + [o['path'] for o in d['outputs'] if o.get('exists')]
    paths += [s['path'] for s in d['live_rig']['sources']]
    paths += [e['path'] for s in r['sections'] for k in ('pages', 'reports', 'media') for e in s[k] if e.get('exists', True)]
    bad = 0; seen = set()
    for p in paths:
        if p in seen: continue
        seen.add(p); url = base + urllib.parse.quote(p)
        try:
            req = urllib.request.Request(url, method='HEAD')
            with urllib.request.urlopen(req, timeout=15) as resp: code, ct = resp.status, resp.headers.get('Content-Type', '')
        except urllib.error.HTTPError as e: code, ct = e.code, ''
        except Exception as e: code, ct = 0, str(e)
        if code != 200: bad += 1; print('BROKEN', code, p)
        elif p.endswith('.mp4') and 'video/mp4' not in ct: bad += 1; print('BAD TYPE', ct, p)
    print(f'checked {len(seen)} paths, {bad} broken')
    return bad

def main(a):
    if not a or a[0] in ('-h', '--help'): print(__doc__); return
    d = load(); cmd = a[0]
    if cmd == 'md': md(d); return
    if cmd == 'register': register(a); return
    if cmd == 'check': sys.exit(1 if check(a[1] if len(a) > 1 else 'http://127.0.0.1:8765/') else 0)
    if cmd == 'touch': pass
    elif cmd == 'move':
        if len(a) < 3 or a[2] not in STATES: sys.exit('usage: move TEXT ' + '|'.join(STATES) + ' [--stay]')
        s, it, parent = find(d, a[1]); it['state'] = a[2]
        if parent is None and '--stay' not in a:
            dest = section(d, STATE_SECTION[a[2]])
            if dest is not s: s['items'].remove(it); dest['items'].append(it)
            print(f"{it['text'][:60]!r} -> {a[2]} in {dest['id']}")
        else: print(f"{it['text'][:60]!r} -> {a[2]}")
    elif cmd == 'add':
        st = a[3] if len(a) > 3 else {'built': 'done', 'progress': 'wip', 'blockers': 'blocked', 'next': 'todo'}.get(a[1], 'todo')
        section(d, a[1])['items'].append({'text': a[2], 'state': st})
    elif cmd == 'progress':
        d['progress']['pct'] = int(a[1])
        if len(a) > 2: d['progress']['label'] = a[2]
    elif cmd == 'owner':
        o = next((o for o in d['owners'] if o['name'].lower() == a[1].lower()), None)
        if not o: sys.exit('unknown owner')
        o['latest'] = a[2]
        if len(a) > 3: o['state'] = a[3]
    elif cmd == 'scan': scan(d); scan_reg()
    elif cmd == 'build':
        if len(a) < 3: sys.exit('usage: build TAB TEXT   (TAB: status|preview|body|eyes|mouth|hands|hair|coder|reference)')
        d.setdefault('build_lines', {})[a[1]] = a[2]
    else: sys.exit(__doc__)
    touch(d); save(d); md(d); print('updated', d['updated_pt'])

if __name__ == '__main__': main(sys.argv[1:])
