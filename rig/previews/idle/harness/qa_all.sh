#!/bin/bash
cd /workspace/shadowveil/rig/previews/idle
for n in "$@"; do for try in 1 2 3; do if python3 harness/qa.py $n ${QADIR:-qa} > work/$n.qa.log 2>&1; then echo "QA $n ok"; break; fi; echo "QA RETRY $n"; sleep 5; done; done
echo QADONE
