#!/usr/bin/env python3
"""Curl every static image/video URL the #reference section uses (original root-absolute form and fixed form)."""
import json, re, subprocess, sys
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8765'
PUB = 'reference/grok_build/public/'
urls = set()
src = open(PUB + 'clean-room/index.html').read()
urls |= set(re.findall(r'"(/clean-room/[^"?]+\.(?:png|jpe?g|webp|gif|mp4|webm|mov|json))', src))
rig = json.load(open(PUB + 'clean-room/rig/apose.json'))
urls |= {p['src'] for p in rig['parts'] if p.get('src')} | {rig['src']}
urls |= {'/reference/grok_build/public/apose.png', '/reference/grok_build/public/tpose.png'}  # clean-room.html bare srcs (orig)
reg = json.load(open('app/registry.json'))
sec = [s for s in reg['sections'] if s['id'] == 'reference'][0]
media = {'/' + m['path'] for m in sec['media']}
def fixed(u):
    if u.startswith('/clean-room/'): return '/' + PUB + u[1:]
    if u in ('/reference/grok_build/public/apose.png', '/reference/grok_build/public/tpose.png'): return u.replace('public/', 'public/clean-room/')
    return u
def curl(u):
    o = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{content_type} %{size_download}', B + u], capture_output=True, text=True).stdout.split()
    return o
rows = []; bad_orig = bad_fix = 0
for u in sorted(urls | media):
    a = curl(u); fx = fixed(u); b = curl(fx) if fx != u else a
    okf = b[0] == '200' and (b[1].startswith(('image/', 'video/')) or b[1].startswith('application/json'))
    bad_orig += a[0] != '200'; bad_fix += not okf
    rows.append(f"{a[0]} -> {b[0]} {b[1]:<18} {b[2]:>9}  {u}" + ('' if fx == u else f"  => {fx}"))
print('\n'.join(rows)); print(f'TOTAL {len(rows)} urls; original-form non-200: {bad_orig}; fixed-form bad: {bad_fix}')
