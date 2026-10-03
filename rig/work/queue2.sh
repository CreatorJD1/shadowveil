#!/bin/bash
cd /workspace/shadowveil/rig/work
while ! grep -q DONE rerun.log; do sleep 10; done
./md5gate.sh 8795 >> queue2.log && PORT=8795 node hairless/hl_check.js apose,tpose,left,right,back '&quality=linear' > hairless/def_official_2345.json 2> hairless/def_official_2345.err
./md5gate.sh 8795 >> queue2.log && PORT=8795 node hairless/hl_check.js apose,tpose,left,right,back '&headgroup=1&quality=linear' > headgroup/rest_hg_2345.json 2> headgroup/rest_hg_2345.err
./md5gate.sh 8795 >> queue2.log && (cd headgroup/renders_2345 && PORT=8795 node ../hg_render.js apose,left,back,right . > ../hg_render_2345.json 2> ../hg_render_2345.err)
./md5gate.sh 8795 >> queue2.log; echo DONE2 >> queue2.log
