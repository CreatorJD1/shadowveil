#!/usr/bin/env bash
# Base Hair speck fix: APPLY (manual only). Do NOT run until Base Body posts that the rebuild is done and the lineart gate
# (hair/qa/lineart/SUMMARY.md) is resolved or waived.
#   bash hair/staged/speck_fix/apply.sh --apply
# 1) preflight: live files unchanged since staging (sha256 in manifest.json); base_body.png and base_body_skin.png are alpha 0
#    at every speck px (Base Body cleared them); staged files present
# 2) backs up the live files to hair/backups/speck_fix_<timestamp>/ (same relative paths) + restore.sh
# 3) copies the staged strands, erase masks and staged validate_hair.py in
# 4) runs python3 rig/rest_check.py and python3 hair/validate_hair.py, then the lineart check (hair/qa/lineart/work/lineart_check.py)
#    before/after; if rest != 0 px in any view, the validator does not print ALL PASS, or any part/joint newly fails the
#    lineart check, it restores the backup and exits 1. (As staged today the lineart gate WILL fail: see SIMULATION.md.)
set -euo pipefail
if [[ "${1:-}" != "--apply" ]]; then
  echo "Staged only. Nothing done. Run with --apply once Base Body says the rebuild is in (see PIXELS.md)." >&2; exit 2
fi
ROOT=/workspace/shadowveil; ST=$ROOT/hair/staged/speck_fix
cd "$ROOT"
TS=$(date +%Y%m%d_%H%M%S); BK=$ROOT/hair/backups/speck_fix_$TS
mapfile -t FILES < <(python3 -c "import json;[print(f['staged']) for f in json.load(open('$ST/manifest.json'))['files']]")
# ---- 1) preflight (read-only)
python3 - "$ST" <<'PY'
import json,sys,hashlib,numpy as np
from PIL import Image
st=sys.argv[1]; m=json.load(open(st+'/manifest.json')); bad=[]
for f in m['files']:
    if hashlib.sha256(open(f['staged'],'rb').read()).hexdigest()!=f['live_sha256_at_staging']: bad.append('live changed since staging: '+f['staged'])
    if hashlib.sha256(open(st+'/'+f['staged'],'rb').read()).hexdigest()!=f['staged_sha256']: bad.append('staged file changed: '+f['staged'])
for v in ['apose','tpose','left','right','back']:
    add=np.array(Image.open(f'{st}/for_base_body/{v}_speck_px_ADD.png'))>127
    for b in ('base_body.png','base_body_skin.png'):
        a=np.array(Image.open(f'views/{v}/{b}').convert('RGBA'))[...,3]
        n=int((add&(a>0)).sum())
        if n: bad.append(f'{v}/{b}: {n} speck px still opaque (Base Body has not cleared them)')
if bad: print('PREFLIGHT FAILED, nothing changed:\n  '+'\n  '.join(bad)); sys.exit(1)
print('preflight OK')
PY
# ---- 2) backup
mkdir -p "$BK"
for f in "${FILES[@]}" hair/validate_hair.py hair/validation.json; do mkdir -p "$BK/$(dirname "$f")"; cp -p "$f" "$BK/$f"; done
{ echo '#!/usr/bin/env bash'; echo "# restore the pre-speck-fix live files"; echo "set -euo pipefail; cd $ROOT"
  for f in "${FILES[@]}" hair/validate_hair.py hair/validation.json; do echo "cp -p '$BK/$f' '$f'"; done; } > "$BK/restore.sh"
chmod +x "$BK/restore.sh"; echo "backup: $BK"
# lineart baseline on the live hair before the copy (writes only into the backup dir)
python3 hair/qa/lineart/work/lineart_check.py --tag pre --hairroot views --out "$BK/lineart" > "$BK/lineart_pre.log"
# ---- 3) copy staged in
for f in "${FILES[@]}"; do cp "$ST/$f" "$f"; done
cp "$ST/validate_hair.py" hair/validate_hair.py
# ---- 4) checks (one at a time)
python3 rig/rest_check.py > "$BK/rest_after.json"
python3 hair/validate_hair.py > "$BK/validate_after.txt" 2>&1 || true
REST_OK=$(python3 -c "import json;d=json.load(open('$BK/rest_after.json'));print(int(all(d[v]['total']==0 for v in d)))")
VAL_OK=$(tail -1 "$BK/validate_after.txt" | grep -qx 'ALL PASS' && echo 1 || echo 0)
python3 hair/qa/lineart/work/lineart_check.py --tag post --hairroot views --out "$BK/lineart" > "$BK/lineart_post.log"
# lineart gate: no part or joint may fail after the apply that passed before it (no new width / break / kink failures)
LINE_OK=$(python3 -c "
import json;a=json.load(open('$BK/lineart/lineart_pre.json'));b=json.load(open('$BK/lineart/lineart_post.json'))
new=[(v,k,n) for v in a for k in ('parts','joints') for n in a[v][k] if a[v][k][n]['PASS'] and not b[v][k][n]['PASS']]
print(int(not new)); import sys; [print('  new lineart fail:',x,file=sys.stderr) for x in new]")
echo "rest 0 px in all views: $REST_OK   validator ALL PASS: $VAL_OK   no new lineart fails: $LINE_OK"
if [[ "$REST_OK" != 1 || "$VAL_OK" != 1 || "$LINE_OK" != 1 ]]; then
  echo "CHECK FAILED: restoring backup" >&2; bash "$BK/restore.sh"; exit 1
fi
echo "applied. logs: $BK/rest_after.json, $BK/validate_after.txt"
