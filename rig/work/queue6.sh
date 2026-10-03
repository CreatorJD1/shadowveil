#!/bin/bash
cd /workspace/shadowveil/rig/work
while pgrep -f "render_hg.py" >/dev/null; do sleep 10; done
cp backup_post6d5b239/index_pre_hairsub_0105.html ../index_qa_backup.html
./md5gate.sh 8795 >> queue6.log && PORT=8795 node partmesh_pilot/default_same.js > hgsubhair/default_same.json 2> hgsubhair/default_same.err
rm -f ../index_qa_backup.html
for q in quality=linear headgroup=1\&quality=linear headgroup=1\&hairless=1\&quality=linear; do t=$(echo $q | tr '&=' '__')
 ./md5gate.sh 8795 >> queue6.log && PORT=8795 node hairless/hl_check.js apose,tpose,left,right,back "&$q" > hgsubhair/rest_$t.json 2> hgsubhair/rest_$t.err; done
./md5gate.sh 8795 >> queue6.log && (cd headgroup && PORT=8795 node hg_sub_rest.js > ../hgsubhair/hg_sub_rest.json 2> ../hgsubhair/hg_sub_rest.err)
./md5gate.sh 8795 >> queue6.log; echo DONE6 >> queue6.log
