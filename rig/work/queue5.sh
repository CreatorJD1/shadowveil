#!/bin/bash
cd /workspace/shadowveil/rig/work
(cd headgroup && ../md5gate.sh 8795 > hg_sub_check_0025.md5 && PORT=8795 node hg_sub_check.js > hg_sub_check_0025.json 2> hg_sub_check_0025.err)

cp backup_post6d5b239/index_pre_mouthfix_2324.html ../index_qa_backup.html
./md5gate.sh 8795 >> queue5.log && PORT=8795 node partmesh_pilot/default_same.js > partmesh_pilot/default_same_0025.json 2> partmesh_pilot/default_same_0025.err
rm -f ../index_qa_backup.html
./md5gate.sh 8795 >> queue5.log && PORT=8795 node hairless/hl_check.js apose,tpose,left,right,back '&hairless=1&quality=linear' > hairless/hl_official_0025.json 2> hairless/hl_official_0025.err
./md5gate.sh 8795 >> queue5.log && PORT=8795 node hairless/hl_check.js apose,tpose,left,right,back '&quality=linear' > hairless/def_official_0025.json 2> hairless/def_official_0025.err
./md5gate.sh 8795 >> queue5.log; echo DONE5 >> queue5.log
