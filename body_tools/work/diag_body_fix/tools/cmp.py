import sys, subprocess; sys.path.insert(0,'.'); from posekit import *
ang = sys.argv[1]
for j in sys.argv[2].split(','):
    for w in ('old', 'new'): subprocess.run(['python3', 'look.py', ang, w, j], capture_output=True)
    a = Image.open(f'_look_{ang}_old_{j}.png'); b = Image.open(f'_look_{ang}_new_{j}.png')
    o = Image.new('RGB', (a.width, a.height + b.height + 10), 'white'); o.paste(a, (0, 0)); o.paste(b, (0, a.height + 10)); o.save(f'_cmp_{ang}_{j}.png')
