#!/bin/bash
cd /workspace/shadowveil/rig/work
G=./md5gate.sh
$G 8795 > rerun.log && PORT=8795 node hairless/hl_check.js apose,tpose,left,right,back '&quality=linear' > hairless/def_official_2340.json 2> hairless/def_official_2340.err; $G 8795 >> rerun.log
# replay of the 22:54 config (pre-edit page copy) on the right tree
PORT=8795 PAGE=index_qa_backup.html node hairless/hl_check.js apose,tpose,left,right,back '&hairless=1&quality=linear' > hairless/hl_2254replay_2340.json 2> hairless/hl_2254replay_2340.err
PORT=8795 node partmesh_pilot/default_same.js > partmesh_pilot/default_same_2340.json 2> partmesh_pilot/default_same_2340.err; $G 8795 >> rerun.log
echo DONE >> rerun.log
