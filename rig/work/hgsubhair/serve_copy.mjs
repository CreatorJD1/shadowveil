// scratch server rooted at /workspace/shadowveil; /rig/index.html is served from the candidate copy (smoke test before moving it in)
import http from 'node:http';import fs from 'node:fs';import path from 'node:path';
const ROOT='/workspace/shadowveil',PORT=+process.argv[2],CAND=process.argv[3];const MT={'.html':'text/html','.json':'application/json','.png':'image/png','.js':'text/javascript'};
http.createServer((q,r)=>{const u=decodeURIComponent(q.url.split('?')[0]);let f=u==='/rig/index.html'&&CAND?CAND:path.join(ROOT,u);if(!f.startsWith(ROOT)){r.writeHead(403);return r.end()}
 fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);return r.end()}r.writeHead(200,{'Content-Type':MT[path.extname(f)]||'application/octet-stream'});r.end(d)})}).listen(PORT,'127.0.0.1');
