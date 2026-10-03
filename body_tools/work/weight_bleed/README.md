# Profile weight bleed (Base Body, STAGED, Sat Oct 3 2026 PT) - option works for the gate, but FAILS the no-visible-change rule
build_skin_xlimb.py = copy of body_tools/build_skin.py + --zero-cross-limb (moves weight on a bone unrelated to the vertex's owner/dominant bone onto the related bone on the tree path, here torso<->forearm -> upperArm); refuses to write outside this folder.
Without the flag it reproduces live views/<view>/body/skin.json exactly (left/right_skin_ref*.json: vertices, triangles, weights identical).
The 9 / 21 bleeding vertices are at the ELBOW over the torso (y 630-644), not at the hip: left v8200-8202,8209-8211,8218-8220 (x686-702,y642) forearm_L<-torso 8 + torso<-forearm_L 1;
right v10719,10886-10893,11039-11040,11047,11059-11066,11221-11231 (x670-688,y630-644) torso<-forearm_R 14 + forearm_R<-torso 7.
Gates (qa_gates --gate weights): bleed left 9 -> 0, right 21 -> 0; texel-owner info 323 -> 315, 340 -> 327; isolation unchanged (upperArm_L 113, forearm_L 118, thigh_L 52; upperArm_R 114, forearm_R 141 -> 136, thigh_R 59) - these are the forearm-over-hip/thigh verts, G1 still FAILS on them.
Browser rig (browser_live_vs_xlimb.json, sheet_browser_live_vs_xlimb.png): rest 0 px; ShoulderL+-1 68/175 px changed, ShoulderL-1+ElbowL-1 458 px + 48 new holes; ShoulderR+1+ElbowR+1 882 px + 48 new holes; vertex moves up to 23.7 / 30.7 px (posedelta json).
=> visible shape change: candidate skins kept only in REJECTED_visible_change/, not staged as a fix.
