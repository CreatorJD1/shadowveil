#!/bin/bash
# usage: render_retry.sh <outdir> <view> [render_idle args...]; retries (resuming finished frames) until meta.json exists
out=$1; view=$2; shift 2
cd /workspace/shadowveil/rig/previews/idle
for i in 1 2 3 4 5 6; do
  rm -f "$out/meta.json"
  node harness/render_idle.mjs "$view" "$out" --resume=1 "$@" >> "$out.log" 2>&1
  [ -s "$out/meta.json" ] && { echo "done $out (attempt $i)" >> "$out.log"; exit 0; }
  echo "retry $i $out" >> "$out.log"; sleep 5
done
exit 1
