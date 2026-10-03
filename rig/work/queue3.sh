#!/bin/bash
cd /workspace/shadowveil/rig/work
while ! grep -q DONE2 queue2.log; do sleep 10; done
./md5gate.sh 8795 >> queue3.log && PORT=8795 node partmesh_pilot/default_same.js > partmesh_pilot/default_same_2350.json 2> partmesh_pilot/default_same_2350.err
./md5gate.sh 8795 >> queue3.log; echo DONE3 >> queue3.log
