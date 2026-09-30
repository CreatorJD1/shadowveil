# Rest check (contract v1.2): composite every view at rest exactly like rig/index.html and compare with base.png.
# Mirrors the renderer: global layer bands (legacy numbering mapped into draw-step order), finger frame f0,
# body/rig.json jointed parts when delivered (else base_body.png).
import json,os,sys,re
from PIL import Image
import numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'skin_tools'))
import skinlib
V='views'
SKIN=next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--skin=')),None)   # --skin=draft -> rig/skin_tools/drafts/<view>_skin.json
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def L(p):
    return Image.open(p).convert('RGBA') if p and os.path.exists(p) else None
def J(p):
    try: return json.load(open(p))
    except Exception: return None
def over(dst,src):
    if src is not None: dst.alpha_composite(src)
NO_FACE_VIEWS={'back'}  # eyes/mouth are not read at all for these views (same rule as index.html)
def norm_parts(ps):
    # file:null parts never override/dedupe a part with a file: per id the first entry with a file wins
    if not isinstance(ps,list): return ps
    with_file={p.get('id') for p in ps if isinstance(p,dict) and p.get('file')}; seen=set(); out=[]
    for p in ps:
        if not isinstance(p,dict) or p.get('id') is None: continue
        if p.get('file'):
            if p['id'] in seen: continue
            seen.add(p['id']); out.append(p)
        elif p['id'] not in with_file and ('0:'+p['id']) not in seen: seen.add('0:'+p['id']); out.append(p)
    return out
def part_set(j):
    # empty rig.json / no parts -> None ('no part set'); else a copy with normalised parts
    if isinstance(j,list): j={'parts':j}
    if not isinstance(j,dict): return None
    ps=j.get('parts')
    if not isinstance(ps,list) or not ps: return None
    return {**j,'parts':norm_parts(ps)}
def parts_of(j):
    if isinstance(j,list): return j
    if isinstance(j,dict) and isinstance(j.get('parts'),list): return j['parts']
    return None
BANDS={'hair':[(100,199),(600,699)],'body':[(200,299)],'hands':[(300,399),(210,219)],'eyes':[(400,499)],'mouth':[(500,599)]}
STEP={'hair_back':0,'body':1,'hands':2,'eyes':3,'mouth':4,'hair_front':5}
def in_band(o,l): return isinstance(l,int) and not isinstance(l,bool) and any(a<=l<=b for a,b in BANDS[o])
def is_v12(o,ps):
    d=[p for p in ps if p.get('file')]; return bool(d) and all(in_band(o,p.get('layer')) for p in d)
def by_layer(ps): return sorted(ps,key=lambda p:(p.get('layer') or 0))  # stable
EYE_FALLBACK=[]
def resolve(hair,body,hands,eyes,mouth):
    Z={};S={}
    EYE_FALLBACK.clear()
    if hair:
        if is_v12('hair',hair):
            S['hair']='v1.2'; Z.update({'hair:'+p['id']:p['layer'] for p in hair})
        else:
            S['hair']='legacy'; b=f=0
            for p in hair:
                if p['id']=='hair_back': Z['hair:'+p['id']]=100+min(b,99); b+=1
            for p in by_layer([p for p in hair if p['id']!='hair_back']): Z['hair:'+p['id']]=600+min(f,99); f+=1
    if body:
        if is_v12('body',body): S['body']='v1.2'; Z.update({'body:'+p['id']:p['layer'] for p in body})
        else:
            S['body']='mapped'
            for n,p in enumerate(by_layer(body)): Z['body:'+p['id']]=200+min(n,99)
    else: S['body']='base_body.png'; Z['body:base_body']=220
    if hands:
        ps=hands['parts']
        if is_v12('hands',ps): S['hands']='v1.2'; Z.update({'hands:'+p['id']:p['layer'] for p in ps})
        else:
            S['hands']='legacy'; n=0
            for p in by_layer(ps):
                if p.get('file'): Z['hands:'+p['id']]=300+min(n,99); n+=1
    if eyes:
        # v1.6.1: every eye layer (white, iris, lid frames, lash) is read from the eyes' own rig.json "layer".
        # Only a part without a valid eyes-band integer layer falls back to the renderer's legacy slot (flagged in eyeLayers).
        ps=eyes['parts']; S['eyes']='v1.2' if is_v12('eyes',ps) else 'legacy (rig.json layers where valid)'
        for i,E in enumerate(eyes['eyes']):
            for p in ps:
                if not p['id'].startswith(E+'_'): continue
                s=p['id'][len(E)+1:]; l=p.get('layer')
                if in_band('eyes',l): Z['eyes:'+p['id']]=l
                else:
                    Z['eyes:'+p['id']]=400+i*10+(0 if s in('white','iris') else 1 if s.startswith('lid_') else 2)
                    EYE_FALLBACK.append(p['id'])
    if mouth:
        ps=mouth['parts']
        if is_v12('mouth',ps): S['mouth']='v1.2'; Z.update({'mouth:'+p['id']:p['layer'] for p in ps})
        else: S['mouth']='legacy'; Z.update({'mouth:'+p['id']:500 for p in ps})
    return Z,S
DEF=[150,220,300,400,500,650]
out={}
for v in ['apose','tpose','left','right','back']:
    b=f'{V}/{v}/'; base=L(b+'base.png'); W,H=base.size
    img=Image.new('RGBA',(W,H),(0,0,0,0))
    hair=norm_parts(parts_of(J(b+'hair/rig.json')) or [])
    noface=v in NO_FACE_VIEWS
    hands=part_set(J(b+'hands/rig.json')); eyes=None if noface else part_set(J(b+'eyes/rig.json')); mo=None if noface else part_set(J(b+'mouth/rig.json'))
    if eyes is not None and not isinstance(eyes.get('eyes'),list): eyes['eyes']=[]
    bj=J(b+'body/rig.json')
    body=[p for p in (norm_parts(parts_of(bj)) or []) if p.get('file') and os.path.exists(b+'body/'+p['file'])]
    # v1.4 skin: views/<view>/body/skin.json (or the draft with --skin=draft) replaces the cut body parts
    skin=None; sp=skinlib.skin_path(b.rstrip('/'),v,ROOT,SKIN,bj.get('skin') if isinstance(bj,dict) else None)
    if sp and os.path.exists(sp):
        sj,SV,ST,SL=skinlib.load(sp); errs=skinlib.validate(sj,SV,ST); simg=L(b+sj.get('image','base_body.png'))
        if errs or simg is None: print(f'{v}: skin {sp} rejected: {errs or "image missing"}',file=sys.stderr)
        else: skin=(sj,SV,ST,SL,simg); body=[]
    Z,S=resolve(hair,body,hands,eyes,mo)
    if skin: S['body']='skin'
    items=[]
    def add(z,step,im):
        items.append(((z if isinstance(z,(int,float)) else DEF[step]),step,len(items),im))
    if skin:
        sj,SV,ST,SL,simg=skin; lm,cnt=skinlib.coverage(SV,ST,SL,W,H); sa=np.array(simg)
        for lay in sorted(set(SL.tolist())):
            g=sa.copy(); g[lm!=lay]=0; add(int(lay),STEP['body'],Image.fromarray(g,'RGBA'))
        out_skin={'file':os.path.relpath(sp,ROOT),'uncoveredOpaque':int(((sa[...,3]>0)&(cnt==0)).sum()),'doubleCovered':int((cnt>1).sum())}
        # v1.5 underlay: validated against the rest rule; a valid one is composited at its layer (it must end up fully hidden)
        ul,uerr=skinlib.underlay_load(sj,SV,ST,SL,b.rstrip('/'),W,H)
        if uerr: out_skin['underlay']={'ok':False,'errors':uerr}; print(f'{v}: underlay rejected: {uerr}',file=sys.stderr)
        elif ul is not None:
            r,fp,bad=skinlib.underlay_check(ul,sa,lm,W,H); out_skin['underlay']={k:r[k] for k in r}
            if not r['ok']: print(f'{v}: underlay rejected (rest footprint not fully under alpha-255 main skin above it): {r}',file=sys.stderr)
            elif ul['identityUV']:
                g=ul['img'].copy(); g[~fp]=0; add(ul['layer'],STEP['body'],Image.fromarray(g,'RGBA'))
    elif body:
        for p in body: add(Z['body:'+p['id']],STEP['body'],L(b+'body/'+p['file']))
    else: add(Z['body:base_body'],STEP['body'],L(b+'base_body.png') or base)
    for p in hair:
        if p.get('file'):
            z=Z['hair:'+p['id']]; add(z,STEP['hair_back'] if z<200 else STEP['hair_front'],L(b+'hair/'+p['file']))
    frames={'segments':0,'problems':[]}
    if hands:
        for p in hands['parts']:
            if not p.get('file'): continue
            im=L(b+'hands/'+p['file'])
            if re.match(r'^[LR]_(Thumb|Index|Middle|Ring|Pinky)\d$',p['id']):
                listed=isinstance(p.get('frames'),list) and len(p['frames'])>0
                ents=[e if isinstance(e,dict) else {'file':e} for e in p['frames']] if listed else []
                fr=[]; bad=None
                for e in ents:
                    f=L(b+'hands/'+e['file']) if e.get('file') else None
                    if f is None:
                        if listed: bad=p['id']+': frame file missing '+str(e.get('file'))
                        break
                    fr.append(f)
                ch=next((q for q in hands['parts'] if q.get('parent')==p['id']),None)
                def far(a,x,y): return a is not None and ((a['x'],a['y']) if isinstance(a,dict) else tuple(a))!=(x,y) and np.hypot(((a['x'] if isinstance(a,dict) else a[0])-x),((a['y'] if isinstance(a,dict) else a[1])-y))>=0.01
                if bad: frames['problems'].append(bad+' (renderer ignores frames)')
                elif fr:
                    if any(f.size!=(W,H) for f in fr): frames['problems'].append(p['id']+': frame canvas size')
                    elif im is not None and not np.array_equal(np.array(fr[0]),np.array(im)): frames['problems'].append(p['id']+': f0 != part (renderer ignores frames)')
                    elif far(ents[0].get('pivot'),p.get('pivotX'),p.get('pivotY')) or (ch and far(ents[0].get('childPivot'),ch.get('pivotX'),ch.get('pivotY'))): frames['problems'].append(p['id']+': f0 pivot/childPivot differ from part (renderer ignores frames)')
                    else: frames['segments']+=1; im=fr[0]
            add(Z['hands:'+p['id']],STEP['hands'],im)
    if eyes:
        for E in eyes['eyes']:
            w=L(b+f'eyes/{E}_white.png'); i=L(b+f'eyes/{E}_iris.png'); e=None
            if w is not None:
                e=w.copy()
                if i is not None:
                    a=np.array(w)[...,3:4]/255.0; ia=np.array(i).astype(float); wa=np.array(w).astype(float)
                    ai=ia[...,3:4]/255.0
                    rgb=ia[...,:3]*ai+wa[...,:3]*(1-ai)
                    e=Image.fromarray(np.concatenate([rgb,wa[...,3:4]],-1).astype('uint8'),'RGBA')
            add(Z.get(f'eyes:{E}_white'),STEP['eyes'],e)
            add(Z.get(f'eyes:{E}_lid_0'),STEP['eyes'],L(b+f'eyes/{E}_lid_0.png'))
            add(Z.get(f'eyes:{E}_lash'),STEP['eyes'],L(b+f'eyes/{E}_lash.png'))
    if mo and os.path.exists(b+'mouth/rest.png'): add(Z.get('mouth:mouth_rest',500),STEP['mouth'],L(b+'mouth/rest.png'))
    for *_,im in sorted(items,key=lambda t:t[:3]): over(img,im)
    A=np.array(img).astype(int); B=np.array(base).astype(int)
    both0=(A[...,3]==0)&(B[...,3]==0)
    d=(np.abs(A-B).max(-1)>0)&~both0
    def m(p):
        if not os.path.exists(p): return np.zeros((H,W),bool)
        a=np.array(Image.open(p).convert('RGBA')).astype(int)
        if (a[...,3]<255).any(): return a[...,3]>127
        return a[...,:3].mean(-1)>127
    hm=m(f'hands/{v}_hand_erase_mask.png'); hr=m(f'hair/{v}_hair_erase_mask.png')
    reg={'hand mask':d&hm,'hair mask':d&hr&~hm}
    rest=d&~hm&~hr
    if eyes and isinstance(eyes.get('workRegion'),list) and len(eyes['workRegion'])==4:
        x0,y0,x1,y1=eyes['workRegion']; em=np.zeros_like(d); em[y0:y1+1,x0:x1+1]=True; reg['eye region']=rest&em; rest=rest&~em
    aa=(mo.get('partsBBox') or {}).get('AA') if mo else None
    if aa and len(aa)==4:
        x0,y0,x1,y1=aa; mm=np.zeros_like(d); mm[y0:y1+1,x0:x1+1]=True; reg['mouth region']=rest&mm; rest=rest&~mm
    reg['elsewhere (base_body outside masks)']=rest
    dimg=np.array(base).copy(); dimg[...,:3]//=3; dimg[d]=[255,0,0,255]
    Image.fromarray(dimg.astype('uint8')).save(f'rig/rest_diff_{v}.png')
    out[v]={'total':int(d.sum()),**{k:int(x.sum()) for k,x in reg.items()},'missing':[s for s,j in [('eyes',eyes),('mouth',mo),('hands',hands),('hair',hair or None)] if not j and not (noface and s in('eyes','mouth')) and not (s!='hair' and os.path.exists(b+s+'/rig.json'))],'empty':[s for s,j in [('eyes',eyes),('mouth',mo),('hands',hands)] if not j and not (noface and s in('eyes','mouth')) and os.path.exists(b+s+'/rig.json')],
            'layers':S}
    if eyes:
        el={}
        for E in eyes['eyes']:
            lids=sorted({Z[k] for k in Z if k.startswith(f'eyes:{E}_lid_')})
            el[E]={'white':Z.get(f'eyes:{E}_white'),'iris':Z.get(f'eyes:{E}_iris'),'lid':lids[0] if len(lids)==1 else lids,'lash':Z.get(f'eyes:{E}_lash')}
        out[v]['eyeLayers']=el
        if EYE_FALLBACK: out[v]['eyeLayerFallback']=list(EYE_FALLBACK)
    if frames['segments'] or frames['problems']: out[v]['fingerFrames']=frames
    if skin: out[v]['skin']=out_skin
print(json.dumps(out,indent=1))
