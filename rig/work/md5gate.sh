#!/bin/bash
# usage: md5gate.sh <port> -- asserts served rig/index.html == /workspace/shadowveil/rig/index.html
a=$(curl -s http://127.0.0.1:$1/rig/index.html | md5sum | cut -d' ' -f1); b=$(md5sum /workspace/shadowveil/rig/index.html | cut -d' ' -f1)
[ "$a" = "$b" ] && echo "md5 ok $a ($(date +%H:%M:%S) PT)" || { echo "MD5 MISMATCH served $a file $b"; exit 3; }
