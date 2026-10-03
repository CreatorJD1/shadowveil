#!/bin/bash
# temp views tree = live eyes parts + staged lid frames (render-only; live views/ untouched)
cd /workspace/shadowveil/eyes/work/lashfix
for v in "$@"; do rm -rf tmp/vstaged/$v; mkdir -p tmp/vstaged/$v/eyes; cp /workspace/shadowveil/views/$v/eyes/* tmp/vstaged/$v/eyes/; cp staged/$v/* tmp/vstaged/$v/eyes/; done
