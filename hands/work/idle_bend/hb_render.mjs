// Single-frame renders through the UNCHANGED rig/index.html (its own render(g,rest) path, guarded canvas).
// Serves /workspace/shadowveil read-only; with --hands=<dir>, requests for views/<view>/hands/<file> are served
// from <dir>/<file> when that file exists there (scratch rig.json) -- live files are never written.
// usage: node hb_render.mjs <view> <cases.json> <outdir> [--hands=<dir>] [--port=8791]
import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import http from 'node:http';import fs from 'node:fs';import path from 'node:path';
const [view,casesF,out]=process.argv.slice(2);const opt=Object.fromEntries(process.argv.slice(5).map(a=>a.replace(/^--/,'').split('=')));
const ROOT='/workspace/shadowveil',PORT=+(opt.port||8791),HO=opt.hands||null;
const MT={'.html':'text/html','.json':'application/json','.png':'image/png','.js':'text/javascript'};
const srv=http.createServer((q,r)=>{let u=decodeURIComponent(q.url.split('?')[0]);let f=path.join(ROOT,u);
 const pre='/views/'+view+'/hands/';if(HO&&u.startsWith(pre)){const s=path.join(HO,u.slice(pre.length));if(fs.existsSync(s))f=s}
 if(!f.startsWith(ROOT)&&!(HO&&f.startsWith(HO))){r.writeHead(403);return r.end()}
 fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);return r.end()}r.writeHead(200,{'Content-Type':MT[path.extname(f)]||'application/octet-stream'});r.end(d)})}).listen(PORT,'127.0.0.1');
const cases=JSON.parse(fs.readFileSync(casesF,'utf8'));fs.mkdirSync(out,{recursive:true});
const J=JSON.parse(fs.readFileSync(ROOT+'/body_tools/idle/idle_clips.json','utf8'));
function keysAt(clip,t){const c=J.clips[clip];const K=Object.assign({},c.keys,(c.viewKeys||{})[view]||{});const o={};let tt=((t%c.duration)+c.duration)%c.duration;
 for(const k in K){const ks=K[k];if(tt<=ks[0][0]){o[k]=ks[0][1];continue}if(tt>=ks[ks.length-1][0]){o[k]=ks[ks.length-1][1];continue}let i=1;while(ks[i][0]<tt)i++;const[t0,v0]=ks[i-1],[t1,v1]=ks[i];o[k]=t1>t0?v0+(v1-v0)*(tt-t0)/(t1-t0):v1}return o}
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-dev-shm-usage','--js-flags=--max-old-space-size=1024']});
const page=await browser.newPage();const logs=[];page.on('pageerror',e=>logs.push('pageerror: '+e.message));page.on('response',r=>{if(r.status()>=400)logs.push('http '+r.status()+' '+r.url())});
await page.goto(`http://127.0.0.1:${PORT}/rig/index.html?view=${view}`,{waitUntil:'networkidle0',timeout:120000});
await page.waitForFunction(()=>typeof R!=='undefined'&&R&&R.z&&R.mouthShapes,{timeout:120000});
const info=await page.evaluate(()=>{mqRunning=true;window.__cv=document.createElement('canvas');__cv.width=W;__cv.height=H;window.__g=guard(__cv.getContext('2d'));
 return{status:document.getElementById('status').textContent,warn:R.warn,frames:Object.keys(R.frames).length,quality:document.getElementById('quality').value}});
if(opt.layers)await page.evaluate(()=>{window.__LAYERS=true});
const meta={view,hands:HO,info,logs,cases:[]};
for(const c of cases){let vals=c.clip?keysAt(c.clip,c.t??(c.frame/30)):{};for(const k in (c.scale||{}))if(k in vals)vals[k]*=c.scale[k];Object.assign(vals,c.vals||{});
 const r=await page.evaluate((vals,rest)=>{for(const k in P)v[k]=P[k][2];hairDrive=null;for(const k in vals)if(k in P)v[k]=vals[k];
  let err=null;try{renderFinal(__g,rest)}catch(e){err=e.message}
  const HM=R.hands?handChain(R.hands.parts,rest?()=>0:handAngle(R.hands),p=>palmExt(p,R._BM||{},rest),rest):{};const ang=R.hands?handAngle(R.hands):null;
  const parts={};if(R.hands)for(const p of R.hands.parts){if(!p.file)continue;const f=frameOf(p,rest);const fr=R.frames[p.id];parts[p.id]={M:HM[p.id],frame:fr?fr.indexOf(f):null,angle:rest?0:ang(p),layer:handLayer(p,rest)}}
  const lay={};if(window.__LAYERS&&R.hands){const cv=document.createElement('canvas');cv.width=W;cv.height=H;const g=guard(cv.getContext('2d'));
   for(const p of R.hands.parts){if(!p.file)continue;const f=frameOf(p,rest);g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,W,H);drawM(g,f?f.img:R.im['hands:'+p.id],HM[p.id]);lay[p.id]=cv.toDataURL('image/png')}}
  const pv={};for(const k in v)if(v[k])pv[k]=+(+v[k]).toFixed(4);return{png:__cv.toDataURL('image/png'),err,parts,params:pv,lay}},vals,!!c.rest);
 fs.writeFileSync(`${out}/${c.name}.png`,Buffer.from(r.png.split(',')[1],'base64'));delete r.png;if(Object.keys(r.lay).length){fs.mkdirSync(`${out}/${c.name}_layers`,{recursive:true});for(const k in r.lay)fs.writeFileSync(`${out}/${c.name}_layers/${k}.png`,Buffer.from(r.lay[k].split(',')[1],'base64'))}delete r.lay;r.name=c.name;meta.cases.push(r);process.stdout.write(c.name+' ')}
fs.writeFileSync(out+'/meta.json',JSON.stringify(meta,null,0));console.log('\ndone',view,'warn',info.warn.length,'logs',logs.length);
await browser.close();srv.close();
