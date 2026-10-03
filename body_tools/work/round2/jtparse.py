import json, re, sys
def parse(path):
    d = json.load(open(path)); out = {'rest': d['rest'], 'qual': d['qual']}
    for deg, s in d['jt'].items():
        cur = None; R = {}
        for line in s.split('\n'):
            m = re.match(r'^(\w+_[LR]) \(x=', line)
            if m: cur = m.group(1); continue
            m = re.match(r'^\s+(skin\+underlay/\w+)\s+holes (\d+) \(rest (\d+)\), tears (\d+).*mean ([\d.]+) \(\d+% of rest ([\d.]+)\).*no-line (\d+)', line)
            if m and cur: R[(cur, m.group(1))] = dict(holes=int(m.group(2)), tears=int(m.group(4)), mean=float(m.group(5)), rest=float(m.group(6)), noline=int(m.group(7)))
            m = re.match(r'^\s+(skin\+underlay/\w+)\s+new holes (\d+) px, new tears (\d+) px.*outline width ([\d.]+)%', line)
            if m: R[('SUMMARY', m.group(1))] = dict(holes=int(m.group(2)), tears=int(m.group(3)), widthPct=float(m.group(4)))
        out[deg] = R
    return out
if __name__ == '__main__':
    for p in sys.argv[1:]:
        o = parse(p); print('==', p, o['qual'], o['rest'])
        for deg in ('25', '12.5'):
            for k, v in sorted(o.get(deg, {}).items()):
                if k[1].endswith(('linear', 'ss2')):
                    extra = f" dmean {v['mean']-v['rest']:+.2f}px" if 'mean' in v else ''
                    print(' ', deg, k[0], k[1], v, extra)
