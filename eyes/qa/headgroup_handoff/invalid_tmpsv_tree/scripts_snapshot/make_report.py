import json,numpy as np,datetime
Q='/workspace/shadowveil/eyes/qa/headgroup_handoff/'
raw=json.load(open(Q+'work/measure_raw.json'))
MOUTH=json.load(open('/workspace/shadowveil/mouth/qa/hairless_headgroup/job2_results.json'))
VIEWOF={'apose_EyeR':'apose','apose_EyeL':'apose','left_EyeL':'left','right_EyeR':'right'}
eyes={}
for k,o in raw.items():
    v=VIEWOF[k];mo=MOUTH[v]['residual']['B_seam_chamfer'][:2];lf=MOUTH[v]['lower_face_crosscheck']
    m={'iris_opening_centroid':o['M1o_iris_opening_centroid'],'iris_green_colour_centroid':o['M1_iris_colour_centroid'] if k.endswith('EyeL') else None,
       'eye_opening_centroid':o['M1p_opening_centroid'],
       'lash_band_centroid':o['lash_band']['centroid_offset'],'upper_lash_chamfer':o['M2_upper_lash_chamfer'][:2],'upper_lash_chamfer_subpx':o['M2_subpx'],
       'all_lid_chamfer':o['M2b_all_lid_chamfer'][:2],'lid_edge_profile':o['M2c_lid_edge_profile'][:2],'eye_luma_ncc':o['M3_eye_luma_ncc'][:2],'eye_luma_ncc_score':o['M3_eye_luma_ncc'][2]}
    core=[m['iris_opening_centroid'],m['lash_band_centroid'],m['eye_luma_ncc']]
    best=[round(float(np.mean([c[0] for c in core])),1),round(float(np.mean([c[1] for c in core])),1)]
    hg=o['headgroup_offset']
    eyes[k]={'view':v,'frame':o['frame'],'eye':'her right, amber' if 'EyeR' in k else 'her left, green','headgroup_offset':hg,
        'methods':m,'best_estimate_residual':best,'best_estimate_rule':'mean of iris_opening_centroid, lash_band_centroid, eye_luma_ncc',
        'total_eye_offset_vs_live':[round(hg[0]+best[0],1),round(hg[1]+best[1],1)],
        'lash_band':o['lash_band'],'cheek_mole_offset':o.get('M4_cheek_mole'),'mole_pos':o.get('mole_pos'),
        'rig_iris_part_centroid':o['rig_iris_part_centroid'],'rig_iris_seg_vs_part':o['M1o_rig_vs_part'],
        'mouth_face_residual':mo,'mouth_lower_face_ncc':lf['D_noseChin_ncc_lipsmasked'][:2],'mouth_lower_face_silhouette':lf['D2_silhouette_edge_chamfer'][:2],
        'eye_minus_mouth':[round(best[0]-mo[0],1),round(best[1]-mo[1],1)],
        'sanity_hg_render_minus_live':o['sanity_hg_minus_live_eye_ncc'],'windows':o['windows'],
        'rejected':{'amber_colour_centroid':o['M1_iris_colour_centroid'] if k.endswith('EyeR') else None,'pupil_dark_core':o['M1b_pupil_dark_core']}}
rep={'title':'Eye handoff offsets with head group','author':'Base Eyes','when':datetime.datetime.now().strftime('%a %b %d %Y %I:%M %p PT'),
 'convention':'residual = turn frame minus rig render (?headgroup=1, all params at default/rest), view px, +x right, +y down. Frame warped into view px with body_tools/work/apose_turn/angle_map.json handoff (base = scale*frame + d).',
 'capture':'headless Chrome (puppeteer-core) http://127.0.0.1:8765/rig/?view=<v>&quality=linear[&headgroup=1]; RigHeadGroup.applyHandoff(view); RigManual(); set all P to default; draw(); FR canvas. caps/ (hg_* and live_*).',
 'eyes':eyes}
json.dump(rep,open(Q+'report.json','w'),indent=1)
for k,e in eyes.items():print(k,e['best_estimate_residual'],'mouth',e['mouth_face_residual'],'eye-mouth',e['eye_minus_mouth'],'total',e['total_eye_offset_vs_live'])
