import json,sys
names=sys.argv[1:];D={n:json.load(open(n)) for n in names}
keys=list(D[names[0]].keys())
print('case'.ljust(16),' | '.join(n.replace('qa_data_','').replace('.json','').ljust(22) for n in names));print(' '*16,' | '.join('kn  pH/pT/pP  hH/hT/hP'.ljust(22) for n in names))
tot={n:[0]*7 for n in names}
for k in keys:
    row=[]
    for n in names:
        r=D[n][k];v=[r['knuckle'],r['pivot_holes'],r['pivot_tears'],r['pivot_partial'],r['hand_holes'],r['hand_tears'],r['hand_partial']];tot[n]=[a+b for a,b in zip(tot[n],v)]
        row.append(f"{v[0]:<3} {v[1]}/{v[2]}/{v[3]}  {v[4]}/{v[5]}/{v[6]}".ljust(22))
    print(k.ljust(16),' | '.join(row))
print('TOTAL'.ljust(16),' | '.join(f"{t[0]:<3} {t[1]}/{t[2]}/{t[3]}  {t[4]}/{t[5]}/{t[6]}".ljust(22) for t in tot.values()))
