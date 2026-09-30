import sys,json
for l in sys.stdin:
    if ' {' not in l: print(l.strip()); continue
    v,j=l.split(' ',1); d=json.loads(j); print(v,'PASS' if d['PASS'] else 'FAIL',{k:d.get(k) for k in ['rig_problems','file_problems','files_unlisted','rest_stack_diff_px','rest_vs_BODY_base_body_diff_px','sway_parts_overlap_px','joint_cap_px','erase_mask_vs_sway_union_mismatch_px','erase_mask_uncovered','part_px_differing_from_base','hair_back_under_soft_px','rest_overlap','forbidden_sources','clamps']})
