# v1.8 part 2 (applied to the output of patch_v18.py): head params HeadTilt/HeadNod with a neck seam gate, hair acceleration input
import sys
src,dst=sys.argv[1],sys.argv[2]
s=open(src).read()
def R(old,new,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'patch anchor found {n}x (want {count}): {old[:90]!r}')
    s=s.replace(old,new)
R("P.RootX=[-40,40,0];P.RootY=[-40,40,0]; // v1.8: root (pelvis) translation in px, whole px on screen; 0 at rest",
  "P.RootX=[-40,40,0];P.RootY=[-40,40,0]; // v1.8: root (pelvis) translation in px, whole px on screen; 0 at rest\n"
  "P.HeadTilt=[-1,1,0];P.HeadNod=[-1,1,0]; // v1.8: head roll x8 deg (+ = clockwise on screen) and pitch x6 deg (+ = chin down), about the neck seam")
R("groups['Root (v1.8, px)']=['RootX','RootY'];","groups['Root (v1.8, px)']=['RootX','RootY'];groups['Head (v1.8)']=['HeadTilt','HeadNod'];")
R("groupBox['Root (v1.8, px)'].style.display=(r.body||r.skin)?'':'none';r.feet=footSetup(r);",
  "groupBox['Root (v1.8, px)'].style.display=(r.body||r.skin)?'':'none';groupBox['Head (v1.8)'].style.display=(r.body||r.skin)?'':'none';r.neck=neckSetup(r);r.feet=footSetup(r);")
R("setBodyUI(false);groupBox['Root (v1.8, px)'].style.display='none';",
  "setBodyUI(false);groupBox['Root (v1.8, px)'].style.display='none';groupBox['Head (v1.8)'].style.display='none';")
R("function rootApply(BM,rest){",
  "// v1.8 head: HeadTilt (roll, 8 deg) and HeadNod (pitch, 6 deg) on the body's head part/bone, about the neck seam centre.\n"
  "// Profiles: nod is a real rotation (forward = the view's facing side), tilt is not drawn (roll is about the line of sight's normal).\n"
  "// Front/back: tilt is a rotation; nod is a vertical offset of HEAD_NOD_PX (+ = down) with no in-plane rotation (that would read as tilt).\n"
  "// Skin: head vertices blend head->torso over NECK_GATE_PX from the seam (renderer-side weights, skin.json untouched), so the seam never opens.\n"
  "const HEAD_TILT_DEG=8,HEAD_NOD_DEG=6,HEAD_NOD_PX=4,NECK_GATE_PX=36;\n"
  "function headFacing(){const vw=document.getElementById('view').value;return vw==='left'?-1:vw==='right'?1:0}\n"
  "function headLocal(){const N=R&&R.neck;if(!N)return null;const t=clamp(v.HeadTilt||0,-1,1),n=clamp(v.HeadNod||0,-1,1);if(!t&&!n)return null;const f=headFacing();\n"
  " if(f)return n?rotAt(N.x,N.y,f*n*HEAD_NOD_DEG):null;return mul(T(0,n*HEAD_NOD_PX),rotAt(N.x,N.y,t*HEAD_TILT_DEG))}\n"
  "function headApply(BM,rest,key){if(rest||!key||!BM[key])return BM;const L=headLocal();if(L)BM[key]=mul(BM[key],L);return BM}\n"
  "function neckSetup(r){const Sk=r.skin;const hb=Sk?Sk.headBone:null;\n"
  " if(!Sk){const hp=r.body&&r.body.parts.find(p=>p.id===((r.body.cfg&&r.body.cfg.headPart)||'head'));return hp?{x:hp.pivotX,y:hp.pivotY,n:0,gated:false,note:'cut parts: no seam gate'}:null}\n"
  " const hi=Sk.bones.findIndex(b=>b.id===hb);if(hi<0)return null;const ti=Sk.bones.findIndex(b=>b.id===Sk.bones[hi].parent);if(ti<0)return null;\n"
  " const dom=(M,i)=>{let b=-1,w=-1;for(let k=0;k<4;k++){if(M.ww[i*4+k]>w){w=M.ww[i*4+k];b=M.wb[i*4+k]}}return b};\n"
  " const cell=new Map(),key=(x,y)=>(Math.floor(x/2)*100003+Math.floor(y/2));for(let i=0;i<Sk.nv;i++)if(dom(Sk,i)!==hi){const k=key(Sk.V[2*i],Sk.V[2*i+1]);if(!cell.has(k))cell.set(k,[]);cell.get(k).push(i)}\n"
  " const seam=[];for(let i=0;i<Sk.nv;i++)if(dom(Sk,i)===hi){const x=Sk.V[2*i],y=Sk.V[2*i+1];let hit=false;for(let a=-1;a<=1&&!hit;a++)for(let b=-1;b<=1&&!hit;b++){const L=cell.get((Math.floor(x/2)+a)*100003+Math.floor(y/2)+b);if(L)for(const j of L)if(Math.hypot(Sk.V[2*j]-x,Sk.V[2*j+1]-y)<=1.5){hit=true;break}}if(hit)seam.push([x,y])}\n"
  " if(!seam.length)return{x:Sk.bones[hi].pivot?Sk.bones[hi].pivot[0]:W/2,y:Sk.bones[hi].pivot?Sk.bones[hi].pivot[1]:H/3,n:0,gated:false,note:'no seam found'};\n"
  " const cx=seam.reduce((a,p)=>a+p[0],0)/seam.length,cy=seam.reduce((a,p)=>a+p[1],0)/seam.length;\n"
  " const gate=M=>{let n=0;for(let i=0;i<M.nv;i++){if(dom(M,i)!==hi)continue;const x=M.V[2*i],y=M.V[2*i+1];let d=1e9;for(const p of seam){const e=Math.hypot(p[0]-x,p[1]-y);if(e<d)d=e}\n"
  "  if(d>=NECK_GATE_PX)continue;const u=d/NECK_GATE_PX,w=Math.fround(u*u*(3-2*u));for(let k=0;k<4;k++){M.wb[i*4+k]=0;M.ww[i*4+k]=0}M.wb[i*4]=hi;M.ww[i*4]=w;M.wb[i*4+1]=ti;M.ww[i*4+1]=Math.fround(1-w);n++}return n};\n"
  " const n=gate(Sk);let nu=0;const U=Sk.underlay;if(U&&U.wb&&U.wb!==Sk.wb&&U.V)nu=gate(U);\n"
  " return{x:cx,y:cy,n:seam.length,gatedVerts:n,gatedUnderlay:nu,gated:true,L:NECK_GATE_PX}}\n"
  "function rootApply(BM,rest){")
R("BM=rootApply(chain(bps,rest?()=>0:bodyAngle,null,p=>p.parent!==undefined?p.parent:BODY_PARENT_OF[p.id]),rest);\n  const hp=R.body.cfg.headPart||(BM.head?'head':'torso');headM=BM[hp]||I;",
  "BM=rootApply(chain(bps,rest?()=>0:bodyAngle,null,p=>p.parent!==undefined?p.parent:BODY_PARENT_OF[p.id]),rest);\n  const hp=R.body.cfg.headPart||(BM.head?'head':'torso');headApply(BM,rest,BM.head||R.body.cfg.headPart?hp:null);headM=BM[hp]||I;")
R("const Sk=R.skin;BM=rootApply(chain(Sk.bones,rest?()=>0:bodyAngle,null,p=>p.parent),rest);headM=BM[Sk.headBone]||BM.head||BM.torso||I;",
  "const Sk=R.skin;BM=headApply(rootApply(chain(Sk.bones,rest?()=>0:bodyAngle,null,p=>p.parent),rest),rest,Sk.headBone);headM=BM[Sk.headBone]||BM.head||BM.torso||I;")
# headPose: read the head angle incl. HeadTilt/HeadNod (the springs react) - root is already in
R("const BM=rootApply(chain(bps,bodyAngle,null,p=>p.parent!==undefined?p.parent:BODY_PARENT_OF[p.id]),false);const hp=R.body.cfg.headPart||(BM.head?'head':'torso');",
  "const BM=rootApply(chain(bps,bodyAngle,null,p=>p.parent!==undefined?p.parent:BODY_PARENT_OF[p.id]),false);const hp=R.body.cfg.headPart||(BM.head?'head':'torso');if(BM[hp]&&hp!=='torso')headApply(BM,false,hp);")
# hair: head acceleration (root motion, lean, head params) as an inertia offset on the chain roots, clamped to +-1
R("const vx=(hp.x-pv.x)/dt,vy=(hp.y-pv.y)/dt,va=(hp.a-pv.a)/dt;A.head=hp;const out={};",
  "const vx=(hp.x-pv.x)/dt,vy=(hp.y-pv.y)/dt,va=(hp.a-pv.a)/dt;A.head=hp;const out={};\n"
  " // v1.8 inertia: low-passed head acceleration (px/s^2); head accelerating up -> hair drops (+y), accelerating right -> hanging tips lag left (+x)\n"
  " {const pv2=A.hv||{x:vx,y:vy};const k=clamp(dt/HAIR_ACC_LP,0,1);A.acc=A.acc||{x:0,y:0};A.acc.x+=((vx-pv2.x)/dt-A.acc.x)*k;A.acc.y+=((vy-pv2.y)/dt-A.acc.y)*k;A.hv={x:vx,y:vy}}\n"
  " const inX=clamp(A.acc.x/HAIR_ACC_FULL*HAIR_ACC_GX,-1,1),inY=clamp(-A.acc.y/HAIR_ACC_FULL,-1,1);")
R("tx=clamp(-hp.a/6,-1,1)*HP.g+0.16*Math.sin(2*Math.PI*0.23*t+ph)+0.07*Math.sin(2*Math.PI*0.61*t+1.7*ph);ty=0.12*Math.sin(2*Math.PI*0.31*t+ph);f=HP.rf;z=HP.rz;",
  "tx=clamp(-hp.a/6,-1,1)*HP.g+0.16*Math.sin(2*Math.PI*0.23*t+ph)+0.07*Math.sin(2*Math.PI*0.61*t+1.7*ph);ty=0.12*Math.sin(2*Math.PI*0.31*t+ph);f=HP.rf;z=HP.rz;\n"
  "   tx=clamp(tx+inX,-1,1);ty=clamp(ty+inY,-1,1);")
R("let HAIR_PRESET='default';let hairClampLog=null;",
  "let HAIR_PRESET='default';let hairClampLog=null;\n// v1.8 inertia input: full offset (1.0) at 1500 px/s^2 of head acceleration, low-pass 0.05 s, horizontal gain 0.5\nconst HAIR_ACC_FULL=1500,HAIR_ACC_LP=0.05,HAIR_ACC_GX=0.5;")
open(dst,'w').write(s);print('ok',len(s))
