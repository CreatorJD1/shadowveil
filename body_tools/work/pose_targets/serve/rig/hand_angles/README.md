# Intermediate hand rigs

Eight live hand meshes: both sides at 45, 135, 225 and 315 degrees. The pinned Shadowveil turn frames f035, f086, f133 and f189 supplied the orientation references and physical hand lengths.

The current PNGs are reconstructed higher resolution artwork, not untouched reference pixels. Generated atlas inputs are preserved in tools/hand-art. tools/install-hd-hands.py extracts the eight sprites, matches the base-model palette, removes transparent fringe, cuts the wrist opening and rebuilds connected finger meshes. Texture density remains approximately 5–6 pixels per reference pixel. tools/calibrate-hand-size.py keeps a shared physical hand length and matches transverse silhouette dimensions to the pinned turn references, then fits the wrist opening locally over the proximal palm. This keeps hand length consistent while allowing narrower profile silhouettes, without letting a narrow wrist cut enlarge the whole hand. Reference measurements are saved in tools/hand-art/reference-size.json. The prior reference extraction generator remains in tools/build-hand-angles.py.

Each mesh has a palm and three joints for each of Thumb, Index, Middle, Ring and Pinky. Curl and spread deform connected weighted triangles. Hidden finger surfaces are not synthesized. At zero curl the full resolution texture is used directly. Posed meshes and focused hand views retain the 2× render buffer. Texture scale metadata keeps attachment coordinates in the original reference space.

The runtime fits the wrist opening and physical hand length with a positive determinant, preserving foreshortening. Hand angles switch opaquely without crossfades. Original Shadowveil source folders and historical contact sheets are unchanged.
