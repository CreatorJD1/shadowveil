import json,sys,os
names=[l.split()[0] for l in open('back_list.txt') if l.strip()]
B=json.load(open('qa_back_c0.json'));M=['pivot_holes','pivot_tears','pivot_partial','hand_holes','hand_tears','hand_partial']
def tot(d,filt=lambda k:True): return [sum(d[k][m] for k in d if filt(k)) for m in M]
b=tot(B)
print('cand  lean(L I/M/R/P) | 0.2 holes L,R | pivot H/T/P | hand H/T/P | max pose |d| | verdict')
for n in names:
    f=f'qa_back_{n}.json'
    if not os.path.exists(f): continue
    D=json.load(open(f));t=tot(D)
    h02=(D['L curl_0.20']['hand_holes'],D['R curl_0.20']['hand_holes'])
    pd=max(abs(D[k][m]-B[k][m]) for k in D if 'pose_' in k for m in M)
    ok=all(x<=y for x,y in zip(t,b)) and pd<=2 and sum(h02)==0
    lean=[l.split()[1:] for l in open('back_list.txt') if l.split()[0]==n][0]
    print(f"{n:4} {'/'.join(lean):16} | {h02[0]:3},{h02[1]:3} | {t[0]}/{t[1]}/{t[2]} | {t[3]}/{t[4]}/{t[5]} | {pd} | {'PASS' if ok else 'fail'}"+('' if ok else ' ('+', '.join(m for m,x,y in zip(M,t,b) if x>y)+(', pose' if pd>2 else '')+(', hole0.2' if sum(h02) else '')+')'))
