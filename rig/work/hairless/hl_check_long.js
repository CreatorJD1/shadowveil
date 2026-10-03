// ?hairless=1 rest check per view: rig Rest check, restPixels vs base, live FR vs base, staged URLs loaded, fallbacks
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');
(async()=>{const views=(process.argv[2]||'apose,tpose,left,right,back').split(','),q=process.argv[3]||'&hairless=1&quality=linear';
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:1800000});const out={};
for(const v of views){const pg=await b.newPage();const errs=[],st=[];pg.on('pageerror',e=>errs.push(String(e)));pg.on('response',r=>{const u=r.url();if(/staged/.test(u))st.push(r.status()+' '+u.replace(/^.*?8765\//,'').replace(/\?v=\d+$/,''))});
 await pg.goto(`http://127.0.0.1:${process.env.PORT||8765}/rig/${process.env.PAGE||"index.html"}?view=${v}${q}`,{waitUntil:'domcontentloaded',timeout:1500000});
 await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:1500000});await new Promise(r=>setTimeout(r,1200));
 out[v]=await pg.evaluate(async()=>{document.getElementById('auto').checked=false;document.getElementById('rest').click();await new Promise(r=>setTimeout(r,300));
  const cmp=(A,B)=>{let n=0;for(let i=0;i<A.length;i+=4){if(A[i+3]===0&&B[i+3]===0)continue;if(A[i]!==B[i]||A[i+1]!==B[i+1]||A[i+2]!==B[i+2]||A[i+3]!==B[i+3])n++}return n};
  const bc=document.createElement('canvas');bc.width=W;bc.height=H;const gb=bc.getContext('2d');gb.drawImage(R.im.base,0,0);const B=gb.getImageData(0,0,W,H).data;
  const rp=cmp(restPixels(),B);draw();const fr=cmp(FR.getContext('2d').getImageData(0,0,W,H).data,B);document.getElementById('check').click();
  return{restCheck:document.getElementById('status').textContent.split('\n')[0],restPixels_vs_base:rp,liveFR_vs_base:fr,fallbacks:window.RigHairless?RigHairless.missing:null}});
 out[v].stagedLoaded=[...new Set(st)];out[v].errors=errs;await pg.close()}
console.log(JSON.stringify(out,null,1));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
