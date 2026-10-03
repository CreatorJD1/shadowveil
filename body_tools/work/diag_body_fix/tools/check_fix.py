"""Run Body's own diag check (diag_body/tools/check_diag.py, unchanged) on the fixed pieces: rest recomposite, palette, chroma, soft alpha,
teammate overlap and the +-25 hole test. Writes checks.json, rest_recomposite_diff.png, joint_test_25.png into diag_body_fix/<ang>/."""
import sys; sys.path.insert(0, '/workspace/shadowveil/body_tools/work/diag_body/tools')
import check_diag
check_diag.OUT = '/workspace/shadowveil/body_tools/work/diag_body_fix'
for a in sys.argv[1:] or ['045', '315']: check_diag.run(a)
