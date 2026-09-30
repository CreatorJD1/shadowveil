import csv, json, sys, traceback
from multiprocessing import Pool
sys.path.insert(0, '.')
import bm
def work(p):
    try:
        r, _ = bm.analyse(p); return r
    except Exception as e:
        return dict(path=p, error=repr(e), faces=[])
if __name__ == '__main__':
    paths = [r['path'] for r in csv.DictReader(open('selected2.csv'))]
    with Pool(6) as pool, open('results.jsonl', 'a') as out:
        for i, r in enumerate(pool.imap_unordered(work, paths, chunksize=4)):
            out.write(json.dumps(r) + '\n')
            if i % 200 == 0: print(i, flush=True)
    print('done')
