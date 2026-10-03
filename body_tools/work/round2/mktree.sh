#!/bin/bash
# Scratch overlay trees for round 2. Team rule: never link rig/ or views/<view>/body/ into scratch; COPY them.
#  rig/      = copy of git HEAD rig/ (no previews/, no work/), so renders use the committed rig and nothing writes back.
#  views/right/body/ = copy (candidates are written here).  Read-only refs (base.png, other views, hands/hair/eyes/mouth) stay linked.
# usage: mktree.sh <tree dir> [staged dir]   (staged dir: its skin.json / base_body_underlay.png / base_body_skin.png are COPIED in)
set -e
T=${1:-/workspace/r2tree}; STG=$2; S=/workspace/shadowveil; G="git --git-dir=/workspace/.shadowveil-git --work-tree=$S"
rm -rf "$T"; mkdir -p "$T/views/right"
for e in $S/*; do n=$(basename "$e"); case $n in views|rig) ;; *) ln -s "$e" "$T/$n";; esac; done
(cd $S && $G archive HEAD rig) | tar -x -C "$T" --exclude='rig/previews' --exclude='rig/work'
for e in $S/views/*; do n=$(basename "$e"); [ "$n" = right ] || ln -s "$e" "$T/views/$n"; done
for e in $S/views/right/*; do n=$(basename "$e"); case $n in body|base_body_skin.png|base_body_underlay.png) ;; *) ln -s "$e" "$T/views/right/$n";; esac; done
cp -a $S/views/right/body "$T/views/right/body"; cp -a $S/views/right/base_body_skin.png $S/views/right/base_body_underlay.png "$T/views/right/"
if [ -n "$STG" ]; then cp "$STG/skin.json" "$T/views/right/body/skin.json"; cp "$STG/base_body_underlay.png" "$STG/base_body_skin.png" "$T/views/right/"; fi
find "$T" -maxdepth 3 -type l | while read l; do case "$(readlink "$l")" in $S/rig*|$S/views/right/body*) echo "BAD LINK $l"; exit 1;; esac; done
echo "tree $T ok"
