import json
for v in ['apose','tpose','left','right']:
    p=f'/workspace/shadowveil/views/{v}/eyes/rig.json'; r=json.load(open(p))
    r['contract']='runtime-contract v1.2'
    r['layerScheme']='v1.2 global layers, eyes band 400-499 (EyeR 400-403, EyeL 410-413: white 0, iris 1, lid frame 2, lash 3)'
    n=sum(1 for q in r['parts'] if q['id'].startswith(r['eyes'][0]+'_lid_'))
    r['lidFrames']=n
    r['lidFrameFiles']={E:[f'{E}_lid_{k}.png' for k in range(n)] for E in r['eyes']}
    r['lidFrameSelection']=f'frame = Math.round((1-<E>Open)*(lidFrames-1)) = Math.round((1-<E>Open)*{n-1}); lid_0 = open (exact drawing), lid_{n-1} = closed'
    for q in r['parts']:
        assert isinstance(q.get('layer'),int) and 400<=q['layer']<=499, q
        E=q['id'].split('_')[0]
        if q['id']==f'{E}_lid_0':
            # informational: same list as the five lid parts; f0 is identical to this part's file (v1.2 frames rule)
            q['frames']=[f'{E}_lid_{k}.png' for k in range(n)]
    r['notes']={
     'lid_0':'exactly her drawn pixels around the opening (binary alpha, identical to base.png) so rest never depends on base_body.png; in profiles it also carries her forward lashes',
     'lid_1..6':'flat sampled skin (median of her skin in a 1-3 px ring around the lid) sliding down from the top of her upper lash band; the lid edge is her sampled lash colour on a smooth curve between her upper and lower lid lines. 8x8 supersampled coverage on edges, 1 px half-alpha skin feather where the lid meets her skin. Frames cover k/7 of the opening area (even 1/7 steps). No shading.',
     'lid_7':'flat skin over every drawn eye pixel near the opening (opening, lash band, lower liner, outline, crease pixels within 7 px, enclosed specks) plus one tapered lash curve along the lower lid. The long crease strokes leaving the eye (toward nose and brow, up to 14 px away) are replaced by copies of her nearest plain skin pixels; brows, moles and the eyeshadow boundary are kept.',
     'lash':'her drawn outer lash wing beyond the opening, cut from base.png, always on top. Profile forward lashes are not in this part (see lid frames).',
     'profileForwardLashes':'profiles: her forward lash pixels are in lid_0 exactly; on lid_1..7 they are hidden with flat skin and redrawn from her own lash pixels shifted down with the lid (root tapered, joined to the lid edge by a short lash-colour bridge)' if v in ('left','right') else 'n/a (front view)',
     'white':'her pixels over the full eye opening; under the drawn iris, copies of her own nearest sclera pixels in the same row',
     'iris':'her drawn iris incl. pupil/catchlight as one part, solid rows, light sclera fringe excluded; integer px offsets only',
     'alpha':'white/iris/lash/lid_0 binary alpha; lid_1..7 partial alpha on edges. All keyed (no #0000FF). *_chroma.png = reference copies composited over #0000FF.'}
    r['notes']['hairClearance']='lid_1..7 never cover a pixel any hair part can occupy over its full sway (rotation chain + swayY, per rig/index.html); crease cover-up keeps >=8 px clear of that swept area and of brow/hair masses'
    if v=='tpose': r['notes']['hairWisp']='the 40 px wisp in hair/tpose_eye_crossing_wisp_mask.png belongs to hair_front (layer 600); it is cut from every EyeR part'
    if v=='apose': r['notes']['lashTrim']='EyeL_lash limited to x<745 (her lash wing only; the hair strip beyond belongs to hair)'
    if v in ('left','right'): r['notes']['profileGaze']='iris sits on the front edge of the opening; the front-edge column keeps her drawn pixel in the white so no sclera patch opens there; travel 1 px (left) / 2 px (right) toward the eye centre and +-1 px vertically'
    json.dump(r,open(p,'w'),indent=1)
print('ok')
