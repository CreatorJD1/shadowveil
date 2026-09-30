# Beauty mark audit — Clean room / Base Body stills

Generated 2026-09-30 PT by the pose-driver worker. Read-only on all art (nothing edited or regenerated).

## Canonical (turn-000, the original A-pose)

Eyeballed at 6x: **one mark under her right (amber) eye** (viewer-left in front views) and **two marks under her left (green) eye** (viewer-right cheek in front views), plus a faint 1-2 px speck just inside the pair that the detector ignores. So "her normal two on the right side of her face" = the viewer-right cheek = her LEFT cheek, under the green eye. Canonical = amber side 1 + green side 2. Crops: turn-000_face.png, t000_head.jpg, t000_cheeks_zoom.png.

## Turnaround stills (layers/rotation, eyeballed; these drive app/driver)

| still | her right (amber) cheek | her left (green) cheek | detector (px, full canvas) | consistent | note |
|---|---|---|---|---|---|
| turn-000 | 1 | 2 | [pair d=68 high] her-left(green)=2@731,244;734,255 her-right(amber)=1@632,247 | true | CANONICAL. Eyeballed: 1 mark under her right (amber) eye, 2 marks under her left (green) eye (viewer-right) plus a faint 1-2 px speck just inside them. |
| turn-045 | 1 | **1** | [pair d=58 high] her-left(green)=1@666,242 her-right(amber)=1@580,246 | **false** | Eyeballed: amber side 1 (ok), green side only 1 mark (canonical 2). The eye still artifacts/turn/fix/eyes-045.jpg is a 2x crop of this same still (NCC 0.997) and also shows 1. |
| turn-090 | not visible (profile) | **0** | [single-green d=48 medium] her-left(green)=0@- | **false** | Eyeballed: profile shows her left (green) cheek with 0 marks (canonical 2). |
| turn-135 | not visible | not visible | - | true (n/a, face turned away) | Back three-quarter; face turned away, marks not visible (expected). |
| turn-180 | not visible | not visible | - | true (n/a, face turned away) | Back; marks not visible (expected). |
| turn-225 | not visible | not visible | - | true (n/a, face turned away) | Back three-quarter; marks not visible (expected). |
| turn-270 | 1 | not visible (profile) | [single-amber d=43 low] her-right(amber)=1@821,228 | true | Eyeballed: profile shows her right (amber) cheek with 1 mark (canonical 1). Detector confidence was low (profile iris), verified by eye. |
| turn-315 | 1 | **1** | [pair d=67 high] her-left(green)=1@771,266 her-right(amber)=1@676,266 | **false** | Eyeballed: amber side 1 (ok), green side only 1 mark (canonical 2). |

Driver consequence: 045, 090 and 315 are **held out** (never a pose target, never blended). Usable: 000, 135, 180, 225, 270.

## Regeneration candidates

### Priority 1 — turnaround stills used by Base Body and the Clean room (eyeballed)

- `reference/grok_build/public/clean-room/layers/rotation/turn-045.png` — Eyeballed: amber side 1 (ok), green side only 1 mark (canonical 2). The eye still artifacts/turn/fix/eyes-045.jpg is a 2x crop of this same still (NCC 0.997) and also shows 1.
- `reference/grok_build/public/clean-room/layers/rotation/turn-090.png` — Eyeballed: profile shows her left (green) cheek with 0 marks (canonical 2).
- `reference/grok_build/public/clean-room/layers/rotation/turn-315.png` — Eyeballed: amber side 1 (ok), green side only 1 mark (canonical 2).
  (their per-angle eye crops artifacts/turn/fix/eyes-045/090/315.jpg and face-045/090/315.jpg are 2x crops of the same pixels and carry the same fault.)

### Priority 2 — every other generated still flagged inconsistent (automated, `consistent=false`)

Full list with per-face counts and pixel positions: `app/qa/beauty_marks/all_stills.csv` (rows with source=art, consistent=false). Contact sheets: `app/qa/beauty_marks/sheets/art_false_*.jpg` (index in sheets/index.json). Counts by folder:

- reference/grok_build/artifacts/imagine_images: 123 (63 high confidence)
- reference/grok_build/public/clean-room/hires: 100 (81 high confidence)
- reference/grok_build_captures: 48 (2 high confidence)
- reference/grok_build (other: assets/attachments/driver-work/freebuff/public root): 13 (3 high confidence)
- reference/apose_turn: 47 (7 high confidence)
- reference/grok_build/public/clean-room/frames: 39 (13 high confidence)
- reference/grok_build/public/clean-room/sheets: 32 (17 high confidence)
- reference/grok_build/artifacts/turn: 23 (11 high confidence)
- reference/grok_build/public/clean-room/layers: 12 (5 high confidence)
- reference: 4 (3 high confidence)
- reference/batch1: 3 (3 high confidence)
- reference/grok_build/public/clean-room/layers/rotation: 3 (all 3 eyeballed: turn-045, turn-090, turn-315)
- reference/grok_build/public/puppet: 3 (0 high confidence)
- hair: 1 (1 high confidence)
- reference/batch2: 1 (0 high confidence)
- reference/grok_build/public/clean-room: 1 (1 high confidence)
- views: 1 (1 high confidence)

High-confidence candidates (face large enough that a 3-4 px mark is unambiguous):

- `hair/backup_pre_quality/base_body/tpose.png` — [pair d=67 high] her-left(green)=1@731,238 her-right(amber)=1@635,240
- `reference/apose_turn/frames/f225.png` — [pair d=45 high] her-left(green)=1@419,193 her-right(amber)=0@-
- `reference/apose_turn/frames/f226.png` — [pair d=46 high] her-left(green)=0@- her-right(amber)=1@352,186
- `reference/apose_turn/frames/f227.png` — [pair d=45 high] her-left(green)=1@418,193 her-right(amber)=1@352,187
- `reference/apose_turn/frames/f230.png` — [pair d=45 high] her-left(green)=0@- her-right(amber)=1@351,186
- `reference/apose_turn/frames/f233.png` — [pair d=45 high] her-left(green)=1@417,193 her-right(amber)=1@350,186
- `reference/apose_turn/frames/f234.png` — [pair d=45 high] her-left(green)=1@416,192 her-right(amber)=1@350,186
- `reference/apose_turn/frames/f235.png` — [pair d=45 high] her-left(green)=1@416,192 her-right(amber)=1@350,186
- `reference/batch1/test_sheet_1db5465b.jpg` — [pair d=82 high] her-left(green)=1@523,281 her-right(amber)=1@402,280 | [pair d=81 high] her-left(green)=1@236,282 her-right(amber)=1@114,281 | [pair d=82 high] her-left(green)=1@809,743 her-right(amber)=1@688,743 | [pair d=81 high] her-left(green)=1@1096,281 her-right(amber)=1@975,280 | [pair d=82 high] her-left(green)=1@232,743 her-right(amber)=1@110,742
- `reference/batch1/test_sheet_9f8eab39.jpg` — [pair d=79 high] her-left(green)=1@305,719 her-right(amber)=0@- | [pair d=78 high] her-left(green)=1@305,249 her-right(amber)=0@- | [pair d=81 high] her-left(green)=1@1154,719 her-right(amber)=1@1036,708
- `reference/batch1/tpose.png` — [pair d=67 high] her-left(green)=1@731,238 her-right(amber)=1@635,240
- `reference/grok_build/artifacts/imagine_images/011e650f-d577-499e-8b19-4dc60fbaf1d3.jpg` — [pair d=78 high] her-left(green)=1@731,312 her-right(amber)=1@620,313
- `reference/grok_build/artifacts/imagine_images/0af8abe3-2552-4ff5-8463-7cd9cd154228.jpg` — [pair d=259 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/1004f535-dec4-4300-8e9b-6b1ee855b65d.jpg` — [pair d=72 high] her-left(green)=1@617,244 her-right(amber)=1@514,245
- `reference/grok_build/artifacts/imagine_images/10fafbba-153f-4b7c-afc3-8887e30d768a.jpg` — [pair d=59 high] her-left(green)=2@648,219;651,230 her-right(amber)=2@561,221;591,239
- `reference/grok_build/artifacts/imagine_images/17241d75-18b7-4cd8-9f27-228c3fc4e172.jpg` — [pair d=254 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/173d08f7-f678-4534-92e5-69572855bc5a.jpg` — [pair d=53 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/1a3c2c9f-6046-4881-b9b0-61aaa0c1b62d.jpg` — [pair d=229 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/1b30d4bc-6da8-4620-8cc6-43a3142a7d65.jpg` — [pair d=64 high] her-left(green)=2@623,296;625,305 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/1db5465b-557f-4dda-aada-ed5eff502dd2.jpg` — [pair d=82 high] her-left(green)=1@523,281 her-right(amber)=1@402,280 | [pair d=81 high] her-left(green)=1@236,282 her-right(amber)=1@114,281 | [pair d=82 high] her-left(green)=1@809,743 her-right(amber)=1@688,743 | [pair d=81 high] her-left(green)=1@1096,281 her-right(amber)=1@975,280 | [pair d=82 high] her-left(green)=1@232,743 her-right(amber)=1@110,742
- `reference/grok_build/artifacts/imagine_images/1dbb05d4-deae-47ee-9a99-44ee723d1f14.jpg` — [pair d=253 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/1e46f5ab-0f8b-4bc8-9942-4ea05f8870c9.jpg` — [pair d=78 high] her-left(green)=2@623,241;626,253 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/20dc9ac4-2226-436f-b807-797b9d7e7cd0.jpg` — [pair d=64 high] her-left(green)=1@769,323 her-right(amber)=2@682,315;676,324
- `reference/grok_build/artifacts/imagine_images/23a855e8-1a2b-4b9b-874a-6e56f9066c72.jpg` — [pair d=76 high] her-left(green)=2@622,238;625,248 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/2481977f-8494-4a8d-8c7b-98b0b6396523.jpg` — [pair d=64 high] her-left(green)=2@617,217;616,228 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/295a412e-1f1d-4246-8264-cbba938381dd.jpg` — [pair d=52 high] her-left(green)=1@610,218 her-right(amber)=1@532,221
- `reference/grok_build/artifacts/imagine_images/29b6ba7c-fd8e-46ab-b522-6d7eacaf971f.jpg` — [pair d=65 high] her-left(green)=1@600,262 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/2b836a7c-14ed-448d-844d-72ac3514977f.jpg` — [pair d=259 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/323034fa-2607-45fe-99bb-4002703ce86e.jpg` — [pair d=73 high] her-left(green)=2@620,228;622,237 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/335bec6c-45bb-4cd0-a7d1-ccead2cb5423.jpg` — [pair d=64 high] her-left(green)=2@624,244;627,253 her-right(amber)=2@533,248;530,256
- `reference/grok_build/artifacts/imagine_images/336f43d4-9237-47b8-b94c-840132a89001.jpg` — [pair d=66 high] her-left(green)=1@550,309 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/409c89ea-574c-425e-a532-595ce03cd6fe.jpg` — [pair d=89 high MIRRORED] her-left(green)=1@509,356 her-right(amber)=1@633,350
- `reference/grok_build/artifacts/imagine_images/411aed3a-7ea1-456b-b1fd-00d885a79e5d.jpg` — [pair d=60 high] her-left(green)=1@593,260 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/41fad7d9-1055-4d56-8f5d-14c078d1269a.jpg` — [pair d=97 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/4713e570-7493-4765-812f-eb70c8c5bc23.jpg` — [pair d=53 high MIRRORED] her-left(green)=1@610,221 her-right(amber)=1@689,221
- `reference/grok_build/artifacts/imagine_images/48ae3632-9c92-4945-b6f4-50b11b3cd8d9.jpg` — [pair d=67 high] her-left(green)=1@623,240 her-right(amber)=1@526,242
- `reference/grok_build/artifacts/imagine_images/6300ee7a-837c-4488-8d25-7d881b312805.jpg` — [pair d=89 high] her-left(green)=2@512,426;516,440 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/6a9ce66d-8202-450d-ace8-e5c14ae07be6.jpg` — [pair d=250 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/6d677e7b-72e5-482f-9957-999334bf16de.jpg` — [pair d=74 high] her-left(green)=1@618,311 her-right(amber)=2@508,315;536,322
- `reference/grok_build/artifacts/imagine_images/6fe3741f-a090-459f-a9bd-1480ab0eb775.jpg` — [pair d=71 high] her-left(green)=1@615,236 her-right(amber)=1@510,247
- `reference/grok_build/artifacts/imagine_images/76a52bd9-6c76-45ce-b81e-1c7014419c08.jpg` — [pair d=69 high] her-left(green)=1@623,245 her-right(amber)=1@523,246
- `reference/grok_build/artifacts/imagine_images/794df9e5-95aa-43f2-81e1-08bd5d8d1d7d.jpg` — [pair d=72 high] her-left(green)=2@562,249;561,261 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/81e0fd24-158d-497b-900f-a52c69d04192.jpg` — [pair d=74 high] her-left(green)=1@616,245 her-right(amber)=1@511,246
- `reference/grok_build/artifacts/imagine_images/846e4260-2589-48b6-952f-429c4a2f504a.jpg` — [pair d=76 high] her-left(green)=1@626,286 her-right(amber)=1@513,286
- `reference/grok_build/artifacts/imagine_images/848c3b7b-ee13-47e7-8a0d-947535fc8f59.jpg` — [pair d=260 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/8daaf191-bc84-4306-9715-4746d92d9e8c.jpg` — [pair d=60 high] her-left(green)=1@650,370 her-right(amber)=1@566,366
- `reference/grok_build/artifacts/imagine_images/9456f7ee-c8cf-443e-b036-2acaf5e3035d.jpg` — [pair d=75 high] her-left(green)=1@488,531 her-right(amber)=2@384,531;378,543
- `reference/grok_build/artifacts/imagine_images/99881c36-20ee-4a42-a297-3bdc9341a886.jpg` — [pair d=257 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/99a78873-f61e-4e33-af68-8fade06e2818.jpg` — [pair d=67 high] her-left(green)=2@623,241;625,250 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/9bc49bf9-aa3b-4f48-aa07-6e63c8680231.jpg` — [pair d=59 high] her-left(green)=1@907,219 her-right(amber)=1@820,221
- `reference/grok_build/artifacts/imagine_images/9cdd8a1e-9a6f-470c-9b47-6693820b2d0d.jpg` — [pair d=112 high] her-left(green)=2@406,394;410,410 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/9e8accf0-3a94-415c-ac47-7ab0db4aee8a.jpg` — [pair d=251 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/9f8eab39-0480-4a16-945d-e435e13ec702.jpg` — [pair d=79 high] her-left(green)=1@305,719 her-right(amber)=0@- | [pair d=78 high] her-left(green)=1@305,249 her-right(amber)=0@- | [pair d=81 high] her-left(green)=1@1154,719 her-right(amber)=1@1036,708
- `reference/grok_build/artifacts/imagine_images/a359ebab-915c-4109-833a-f4d9e109d63c.jpg` — [pair d=176 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/a825c836-25d0-445b-bd00-a306052c2cc6.jpg` — [pair d=264 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/b16ea7d7-9141-46ff-871f-65258880fad5.jpg` — [pair d=248 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/b218fccd-c650-47ca-ad64-7d0c1ffa90d0.jpg` — [pair d=249 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/b5c4008f-0d01-4290-b150-c45e18472720.jpg` — [pair d=69 high] her-left(green)=2@604,268;607,277 her-right(amber)=2@506,269;502,277
- `reference/grok_build/artifacts/imagine_images/b91b79c0-fed0-4bd5-bd11-5b12d52812db.jpg` — [pair d=259 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/bfe93474-d2a6-4c6e-a508-a1b226594c01.jpg` — [pair d=70 high] her-left(green)=2@613,247;616,257 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/c21b2440-d725-4ab7-9535-eafa54a036d0.jpg` — [pair d=72 high] her-left(green)=1@647,222 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/c4bdec8c-ed8b-45aa-8d08-cb4166eb4ba2.jpg` — [pair d=65 high] her-left(green)=1@615,282 her-right(amber)=1@521,284
- `reference/grok_build/artifacts/imagine_images/ca63fbc0-5bda-460e-8137-4ac3a4620145.jpg` — [pair d=98 high] her-left(green)=1@475,499 her-right(amber)=1@342,534
- `reference/grok_build/artifacts/imagine_images/ca9f1dd6-a0d1-40ee-ba4c-a412edf89eaa.jpg` — [pair d=67 high] her-left(green)=1@621,301 her-right(amber)=1@525,300
- `reference/grok_build/artifacts/imagine_images/d42e5be0-9180-4f30-876e-e2d796b48431.jpg` — [pair d=258 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/d4e94ec9-4594-41fe-9ab0-83171c308282.jpg` — [pair d=188 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/ddfb5f89-c485-4aea-a16e-358676bef35d.jpg` — [pair d=70 high] her-left(green)=1@619,238 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/e2ee27e3-a33a-4576-b471-40341b558433.jpg` — [pair d=259 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/e4845873-75dd-412f-995a-fe681c1ea22c.jpg` — [pair d=78 high] her-left(green)=1@639,270 her-right(amber)=1@525,272
- `reference/grok_build/artifacts/imagine_images/e4d5d745-8181-4764-9cf2-64783da93c08.jpg` — [pair d=60 high] her-left(green)=1@706,240 her-right(amber)=1@618,240
- `reference/grok_build/artifacts/imagine_images/e79e7d7f-a7da-4fa9-8633-84fdd8304f7a.jpg` — [pair d=84 high] her-left(green)=2@1592,745;1596,758 her-right(amber)=1@1469,749 | [pair d=86 high] her-left(green)=2@1162,749;1166,762 her-right(amber)=1@1040,752 | [pair d=90 high] her-left(green)=2@1592,274;1596,286 her-right(amber)=1@1469,276 | [pair d=90 high] her-left(green)=2@1162,274;1166,286 her-right(amber)=1@1039,276 | [pair d=86 high] her-left(green)=2@307,744;311,758 her-right(amber)=1@184,745 | [pair d=84 high] her-left(green)=1@740,763 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/ed0b574d-af8f-49c2-90a1-405e5fd87855.jpg` — [pair d=78 high] her-left(green)=2@627,253;630,264 her-right(amber)=0@-
- `reference/grok_build/artifacts/imagine_images/fa46fb16-45b2-4de7-b603-6c3bf5e8fd88.jpg` — [pair d=63 high] her-left(green)=2@607,242;611,251 her-right(amber)=2@517,246;515,254
- `reference/grok_build/artifacts/imagine_images/fd97c26a-9bc3-4519-add6-fa02ab771c65.jpg` — [pair d=259 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/artifacts/turn/apose-face.jpg` — [pair d=47 high] her-left(green)=2@249,214;252,225 her-right(amber)=0@-
- `reference/grok_build/artifacts/turn/face-045.jpg` — [pair d=57 high] her-left(green)=1@236,222 her-right(amber)=1@150,226
- `reference/grok_build/artifacts/turn/face-315.jpg` — [pair d=66 high] her-left(green)=1@341,246 her-right(amber)=1@245,246
- `reference/grok_build/artifacts/turn/face-crop.jpg` — [pair d=65 high] her-left(green)=1@615,126 her-right(amber)=1@521,128
- `reference/grok_build/artifacts/turn/fix/eyes-045.jpg` — [pair d=114 high] her-left(green)=1@292,186 her-right(amber)=1@121,192
- `reference/grok_build/artifacts/turn/fix/eyes-315.jpg` — [pair d=133 high] her-left(green)=1@422,212 her-right(amber)=1@231,213
- `reference/grok_build/artifacts/turn/fix/src-head-045.png` — [pair d=58 high] her-left(green)=1@166,212 her-right(amber)=1@80,216
- `reference/grok_build/artifacts/turn/fix/src-head-315.png` — [pair d=67 high] her-left(green)=1@291,226 her-right(amber)=1@196,226
- `reference/grok_build/artifacts/turn/kneel-1.6.jpg` — [pair d=46 high] her-left(green)=2@418,458;420,465 her-right(amber)=0@-
- `reference/grok_build/artifacts/turn/lock/clean40.jpg` — [pair d=53 high] her-left(green)=1@279,226 her-right(amber)=1@202,228
- `reference/grok_build/artifacts/turn/lock/mesh48.jpg` — [pair d=46 high] her-left(green)=0@- her-right(amber)=1@208,226
- `reference/grok_build/attachments/66514.jpg` — [pair d=50 high] her-left(green)=1@328,338 her-right(amber)=1@250,329
- `reference/grok_build/attachments/66569.jpg` — [pair d=57 high] her-left(green)=0@- her-right(amber)=1@292,208
- `reference/grok_build/attachments/66573.jpg` — [pair d=90 high] her-left(green)=1@630,311 her-right(amber)=2@499,294;488,299
- `reference/grok_build/public/clean-room/frames/emo-2-1.jpg` — [pair d=96 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/frames/emo-2-2.jpg` — [pair d=87 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/frames/emo-2-3.jpg` — [pair d=98 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/frames/faces-locked-1.jpg` — [pair d=86 high] her-left(green)=1@284,277 her-right(amber)=1@156,266
- `reference/grok_build/public/clean-room/frames/faces-locked-6.jpg` — [pair d=84 high] her-left(green)=1@281,278 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/frames/life-1.jpg` — [pair d=63 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/frames/motion-1.jpg` — [pair d=74 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/frames/reactions-1.jpg` — [pair d=72 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/frames/reactions-2-2.jpg` — [pair d=73 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/frames/reactions-2-3.jpg` — [pair d=71 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/frames/reactions-2.jpg` — [pair d=74 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/frames/reactions-4.jpg` — [pair d=63 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/frames/sheet-9f8e-5.jpg` — [pair d=78 high] her-left(green)=1@273,243 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/acts-2-1.jpg` — [pair d=71 high] her-left(green)=1@615,236 her-right(amber)=1@510,247
- `reference/grok_build/public/clean-room/hires/acts-2-2.jpg` — [pair d=69 high] her-left(green)=2@604,268;607,277 her-right(amber)=2@506,269;502,277
- `reference/grok_build/public/clean-room/hires/adjust-3.jpg` — [pair d=73 high] her-left(green)=1@618,251 her-right(amber)=1@515,252
- `reference/grok_build/public/clean-room/hires/adjust-4.jpg` — [pair d=71 high] her-left(green)=2@612,250;612,260 her-right(amber)=2@510,251;506,260
- `reference/grok_build/public/clean-room/hires/emo-2-1.jpg` — [pair d=75 high] her-left(green)=0@- her-right(amber)=1@510,264
- `reference/grok_build/public/clean-room/hires/emo-2-2.jpg` — [pair d=77 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/emo-2-3.jpg` — [pair d=75 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/emotions-1.jpg` — [pair d=70 high] her-left(green)=0@- her-right(amber)=1@520,240
- `reference/grok_build/public/clean-room/hires/emotions-2.jpg` — [pair d=74 high] her-left(green)=1@616,245 her-right(amber)=1@511,246
- `reference/grok_build/public/clean-room/hires/emotions-4.jpg` — [pair d=74 high] her-left(green)=1@620,228 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/emotions-6.jpg` — [pair d=71 high] her-left(green)=2@612,223;615,233 her-right(amber)=2@508,224;502,233
- `reference/grok_build/public/clean-room/hires/emotions-7.jpg` — [pair d=71 high] her-left(green)=2@614,226;617,236 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/faces-locked-1.jpg` — [pair d=72 high] her-left(green)=1@628,266 her-right(amber)=1@523,255
- `reference/grok_build/public/clean-room/hires/faces-locked-3.jpg` — [pair d=78 high] her-left(green)=2@627,253;630,264 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/faces-locked-4.jpg` — [pair d=80 high] her-left(green)=2@627,256;630,267 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/faces-locked-6.jpg` — [pair d=74 high] her-left(green)=1@631,262 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/getup-rise-1.jpg` — [pair d=94 high] her-left(green)=1@642,481 her-right(amber)=1@507,481
- `reference/grok_build/public/clean-room/hires/getup-rise-4.jpg` — [pair d=70 high] her-left(green)=2@622,241;626,252 her-right(amber)=2@520,242;513,250
- `reference/grok_build/public/clean-room/hires/idle-34-1.jpg` — [pair d=67 high] her-left(green)=2@586,247;590,258 her-right(amber)=2@491,252;489,260
- `reference/grok_build/public/clean-room/hires/idle-34-3.jpg` — [pair d=67 high] her-left(green)=2@650,258;654,268 her-right(amber)=2@556,263;586,283
- `reference/grok_build/public/clean-room/hires/idle-front-2.jpg` — [pair d=71 high] her-left(green)=2@624,241;626,252 her-right(amber)=2@522,242;516,251
- `reference/grok_build/public/clean-room/hires/idle-front-3.jpg` — [pair d=71 high] her-left(green)=1@628,238 her-right(amber)=1@524,240
- `reference/grok_build/public/clean-room/hires/idle-front-5.jpg` — [pair d=72 high] her-left(green)=2@623,240;626,250 her-right(amber)=2@520,242;514,250
- `reference/grok_build/public/clean-room/hires/idle-front-7.jpg` — [pair d=73 high] her-left(green)=2@625,236;628,248 her-right(amber)=2@522,237;516,246
- `reference/grok_build/public/clean-room/hires/idle-front-8.jpg` — [pair d=71 high] her-left(green)=1@628,237 her-right(amber)=2@525,239;520,248
- `reference/grok_build/public/clean-room/hires/inspect-1.jpg` — [pair d=64 high] her-left(green)=1@590,260 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/inspect-2.jpg` — [pair d=67 high] her-left(green)=1@597,289 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/interact-2.jpg` — [pair d=67 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/lie-4.jpg` — [pair d=101 high] her-left(green)=1@657,477 her-right(amber)=1@514,478
- `reference/grok_build/public/clean-room/hires/lie-front-1.jpg` — [pair d=96 high] her-left(green)=2@320,768;324,784 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/life-1.jpg` — [pair d=76 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/loop-blink-3.jpg` — [pair d=75 high] her-left(green)=1@626,248 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/motion-1.jpg` — [pair d=78 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/motion-2.jpg` — [pair d=76 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/reactions-1.jpg` — [pair d=79 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/reactions-2-1.jpg` — [pair d=79 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/reactions-2-2.jpg` — [pair d=78 high] her-left(green)=0@- her-right(amber)=1@511,268
- `reference/grok_build/public/clean-room/hires/reactions-2-3.jpg` — [pair d=71 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/reactions-2.jpg` — [pair d=76 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/reactions-4.jpg` — [pair d=71 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/set-16-10p1.jpg` — [pair d=116 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/set-16-10p2.jpg` — [pair d=63 high] her-left(green)=1@601,382 her-right(amber)=1@506,383
- `reference/grok_build/public/clean-room/hires/set-16-11p1.jpg` — [pair d=71 high] her-left(green)=2@663,216;666,224 her-right(amber)=2@565,228;550,240
- `reference/grok_build/public/clean-room/hires/set-16-11p2.jpg` — [pair d=74 high] her-left(green)=0@- her-right(amber)=1@547,273
- `reference/grok_build/public/clean-room/hires/set-16-12.jpg` — [pair d=68 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/set-16-5.jpg` — [pair d=85 high] her-left(green)=2@642,287;645,299 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/set-16-6.jpg` — [pair d=75 high] her-left(green)=2@584,319;585,330 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/set-16-8.jpg` — [pair d=90 high] her-left(green)=1@680,276 her-right(amber)=1@549,277
- `reference/grok_build/public/clean-room/hires/set-17-2.jpg` — [pair d=61 high] her-left(green)=1@579,332 her-right(amber)=1@498,352
- `reference/grok_build/public/clean-room/hires/set-17-3.jpg` — [pair d=70 high] her-left(green)=2@613,247;616,257 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/set-17-4.jpg` — [pair d=97 high] her-left(green)=2@629,294;632,307 her-right(amber)=2@492,295;480,304
- `reference/grok_build/public/clean-room/hires/set-17-6.jpg` — [pair d=62 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/set-18-1p2.jpg` — [pair d=71 high] her-left(green)=1@609,224 her-right(amber)=1@502,225
- `reference/grok_build/public/clean-room/hires/set-18-2p1.jpg` — [pair d=60 high] her-left(green)=2@623,296;625,305 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/set-18-4p1.jpg` — [pair d=71 high] her-left(green)=1@647,222 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/sheet-1947-2.jpg` — [pair d=98 high] her-left(green)=1@475,499 her-right(amber)=1@342,534
- `reference/grok_build/public/clean-room/hires/sheet-1947-4.jpg` — [pair d=65 high] her-left(green)=1@549,236 her-right(amber)=1@475,239
- `reference/grok_build/public/clean-room/hires/sheet-1947-5.jpg` — [pair d=65 high] her-left(green)=1@600,262 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/sheet-1db5-1.jpg` — [pair d=74 high] her-left(green)=1@627,267 her-right(amber)=1@514,266
- `reference/grok_build/public/clean-room/hires/sheet-1db5-11.jpg` — [pair d=72 high] her-left(green)=1@625,239 her-right(amber)=1@516,239
- `reference/grok_build/public/clean-room/hires/sheet-1db5-2.jpg` — [pair d=77 high] her-left(green)=1@626,286 her-right(amber)=1@513,286
- `reference/grok_build/public/clean-room/hires/sheet-1db5-3.jpg` — [pair d=75 high] her-left(green)=1@626,280 her-right(amber)=1@515,279
- `reference/grok_build/public/clean-room/hires/sheet-1db5-4.jpg` — [pair d=76 high] her-left(green)=1@626,272 her-right(amber)=1@512,272
- `reference/grok_build/public/clean-room/hires/sheet-1db5-5.jpg` — [pair d=73 high] her-left(green)=1@628,268 her-right(amber)=1@517,267
- `reference/grok_build/public/clean-room/hires/sheet-1db5-6.jpg` — [pair d=74 high] her-left(green)=1@626,269 her-right(amber)=3@516,269;509,279;514,286
- `reference/grok_build/public/clean-room/hires/sheet-1db5-7.jpg` — [pair d=78 high] her-left(green)=1@630,278 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/sheet-1db5-8.jpg` — [pair d=74 high] her-left(green)=1@628,273 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/sheet-1db5-9.jpg` — [pair d=76 high] her-left(green)=1@626,270 her-right(amber)=1@515,270
- `reference/grok_build/public/clean-room/hires/sheet-9f8e-1.jpg` — [pair d=76 high] her-left(green)=1@628,266 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/sheet-9f8e-2.jpg` — [pair d=73 high] her-left(green)=1@624,255 her-right(amber)=1@510,269
- `reference/grok_build/public/clean-room/hires/sheet-9f8e-3.jpg` — [pair d=81 high] her-left(green)=0@- her-right(amber)=1@497,281
- `reference/grok_build/public/clean-room/hires/sheet-9f8e-4.jpg` — [pair d=82 high] her-left(green)=1@628,276 her-right(amber)=2@510,276;510,288
- `reference/grok_build/public/clean-room/hires/sheet-9f8e-5.jpg` — [pair d=73 high] her-left(green)=1@626,257 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/sheet-9f8e-6.jpg` — [pair d=76 high] her-left(green)=1@628,263 her-right(amber)=1@514,264
- `reference/grok_build/public/clean-room/hires/sheet-9f8e-7.jpg` — [pair d=72 high] her-left(green)=1@615,252 her-right(amber)=1@505,240
- `reference/grok_build/public/clean-room/hires/sheet-9f8e-8.jpg` — [pair d=74 high] her-left(green)=2@624,252;633,261 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/sheet-aab0-1.jpg` — [pair d=72 high] her-left(green)=2@621,250;621,262 her-right(amber)=2@518,251;513,260
- `reference/grok_build/public/clean-room/hires/sheet-aab0-5.jpg` — [pair d=69 high] her-left(green)=2@619,241;622,251 her-right(amber)=2@520,242;514,253
- `reference/grok_build/public/clean-room/hires/sit-more-3.jpg` — [pair d=96 high] her-left(green)=1@676,304 her-right(amber)=1@537,305
- `reference/grok_build/public/clean-room/hires/turnaround-2.jpg` — [pair d=59 high] her-left(green)=1@576,234 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/hires/turnaround-4.jpg` — [pair d=53 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/layers/anim/getup.png` — [pair d=68 high] her-left(green)=2@422,410;425,418 her-right(amber)=2@325,411;321,420
- `reference/grok_build/public/clean-room/layers/anim/hem.png` — [pair d=48 high] her-left(green)=1@413,161 her-right(amber)=1@343,162
- `reference/grok_build/public/clean-room/layers/anim/hip.png` — [pair d=49 high] her-left(green)=1@392,168 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/layers/anim/point.png` — [pair d=49 high] her-left(green)=1@375,166 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/layers/anim/shrug.png` — [pair d=48 high] her-left(green)=1@408,150 her-right(amber)=1@339,151
- `reference/grok_build/public/clean-room/sheets/emo-2.jpg` — [pair d=96 high] her-left(green)=0@- her-right(amber)=0@- | [pair d=98 high] her-left(green)=0@- her-right(amber)=0@- | [pair d=86 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/extreme-hop.jpg` — [pair d=68 high] her-left(green)=2@395,375;399,386 her-right(amber)=2@298,377;296,387
- `reference/grok_build/public/clean-room/sheets/extreme-spin.jpg` — [pair d=61 high] her-left(green)=1@560,286 her-right(amber)=1@476,280
- `reference/grok_build/public/clean-room/sheets/faces-locked.jpg` — [pair d=84 high] her-left(green)=2@1592,745;1596,758 her-right(amber)=1@1469,749 | [pair d=86 high] her-left(green)=1@312,287 her-right(amber)=1@184,276 | [pair d=86 high] her-left(green)=2@1162,749;1166,762 her-right(amber)=1@1040,752 | [pair d=90 high] her-left(green)=2@1592,274;1596,286 her-right(amber)=1@1469,276 | [pair d=90 high] her-left(green)=2@1162,274;1166,286 her-right(amber)=1@1039,276 | [pair d=86 high] her-left(green)=2@307,744;311,758 her-right(amber)=1@184,745 | [pair d=84 high] her-left(green)=1@740,763 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/faces-locked.png` — [pair d=84 high] her-left(green)=2@1592,745;1596,758 her-right(amber)=1@1469,749 | [pair d=86 high] her-left(green)=2@1162,749;1166,762 her-right(amber)=1@1040,752 | [pair d=90 high] her-left(green)=2@1592,274;1596,286 her-right(amber)=1@1469,276 | [pair d=90 high] her-left(green)=2@1162,274;1166,286 her-right(amber)=1@1039,276 | [pair d=86 high] her-left(green)=2@307,744;311,758 her-right(amber)=1@184,745 | [pair d=84 high] her-left(green)=1@740,763 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/jump-3.jpg` — [pair d=83 high] her-left(green)=2@652,310;656,321 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/jump-6.jpg` — [pair d=112 high] her-left(green)=2@406,394;410,410 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/lie-front.jpg` — [pair d=89 high] her-left(green)=2@326,322;331,336 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/life.jpg` — [pair d=59 high] her-left(green)=2@670,208;672,217 her-right(amber)=1@585,210 | [pair d=58 high] her-left(green)=2@1080,198;1082,208 her-right(amber)=1@996,200 | [pair d=63 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/loop-talk.jpg` — [pair d=68 high] her-left(green)=2@946,200;949,208 her-right(amber)=1@849,201 | [pair d=66 high] her-left(green)=2@225,200;227,210 her-right(amber)=1@127,202 | [pair d=68 high] her-left(green)=2@1308,205;1310,214 her-right(amber)=0@- | [pair d=67 high] her-left(green)=2@586,205;588,214 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/motion.jpg` — [pair d=74 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/play-point.jpg` — [pair d=72 high] her-left(green)=2@562,249;561,260 her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/play.jpg` — [pair d=165 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/reactions-2.jpg` — [pair d=73 high] her-left(green)=0@- her-right(amber)=0@- | [pair d=71 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/reactions.jpg` — [pair d=73 high] her-left(green)=0@- her-right(amber)=1@480,244 | [pair d=71 high] her-left(green)=0@- her-right(amber)=0@- | [pair d=64 high] her-left(green)=0@- her-right(amber)=0@-
- `reference/grok_build/public/clean-room/sheets/sheet-1db5.jpg` — [pair d=82 high] her-left(green)=1@523,281 her-right(amber)=1@402,280 | [pair d=81 high] her-left(green)=1@236,282 her-right(amber)=1@114,281 | [pair d=82 high] her-left(green)=1@809,743 her-right(amber)=1@688,743 | [pair d=81 high] her-left(green)=1@1096,281 her-right(amber)=1@975,280 | [pair d=82 high] her-left(green)=1@232,743 her-right(amber)=1@110,742
- `reference/grok_build/public/clean-room/sheets/sheet-9f8e.jpg` — [pair d=79 high] her-left(green)=1@305,719 her-right(amber)=0@- | [pair d=78 high] her-left(green)=1@305,249 her-right(amber)=0@- | [pair d=81 high] her-left(green)=1@1154,719 her-right(amber)=1@1036,708
- `reference/grok_build/public/clean-room/tpose.png` — [pair d=67 high] her-left(green)=1@731,238 her-right(amber)=1@635,240
- `reference/grok_build_captures/stills/brace_t5.3s.png` — [pair d=50 high] her-left(green)=1@335,140 her-right(amber)=1@263,141
- `reference/grok_build_captures/tabs/stills_Ground.png` — [pair d=55 high] her-left(green)=1@339,476 her-right(amber)=0@-
- `reference/test_sheet_expressions.jpg` — [pair d=79 high] her-left(green)=1@305,719 her-right(amber)=0@- | [pair d=78 high] her-left(green)=1@305,249 her-right(amber)=0@- | [pair d=81 high] her-left(green)=1@1154,719 her-right(amber)=1@1036,708
- `reference/test_sheet_face_shapes.jpg` — [pair d=82 high] her-left(green)=1@523,281 her-right(amber)=1@402,280 | [pair d=81 high] her-left(green)=1@236,282 her-right(amber)=1@114,281 | [pair d=82 high] her-left(green)=1@809,743 her-right(amber)=1@688,743 | [pair d=81 high] her-left(green)=1@1096,281 her-right(amber)=1@975,280 | [pair d=82 high] her-left(green)=1@232,743 her-right(amber)=1@110,742
- `reference/tpose.png` — [pair d=67 high] her-left(green)=1@731,238 her-right(amber)=1@635,240
- `views/tpose/base.png` — [pair d=67 high] her-left(green)=1@731,238 her-right(amber)=1@635,240

Medium-confidence candidates are listed in the CSV only (confidence=medium).

### Uncertain (face too small / profile iris; needs a human look)

196 art stills, see sheets/art_uncertain_*.jpg and the CSV (consistent=uncertain).

## Totals

Audited 2442 images (1956 generated art, 486 derived tool/QA output under */work/, /tmp, artifacts QA folders). Scope: the parallel inventory's 1,323 full-figure/face stills (/tmp/all_stills.csv) plus every png/jpg >=160 px under reference/ (grok_build public/clean-room + artifacts incl. turn and imagine_images, batch1, batch2, apose_turn, grok_build_captures) and other shadowveil stills; layer/part cuts, rig parts, .vercel copies, backups and node_modules skipped.

| source | consistent | inconsistent | uncertain | n/a (no visible face/cheek) |
|---|---|---|---|---|
| art | 227 | 454 | 196 | 1079 |
| derived | 79 | 160 | 69 | 178 |

Note: reference/batch2 holds 3 group sheets (test_sheet_*.jpg) with faces ~15-20 px apart, too small to count marks reliably; they come out uncertain/false with low-medium confidence.

## Method

tools/bm.py: find her irises by colour (green = her left eye, amber = her right eye; each needs sclera, lash and pupil pixels next to it), pair them into faces (single-eye faces for profiles), build a cheek window under each eye scaled by the eye distance d (0.16-0.66 d below, 0.55 d outward to 0.28 d inward), keep skin pixels, and count small round isolated dark blobs (area >= 3 px scaled by (d/67)^2, <= 0.11 d across, aspect <= 2.6, mean luminance <= 0.47 x local skin, >= 60% skin ring). Mirrored images (amber on viewer-right in a level face) are flagged. Confidence: high d>=45 px, medium 28-45, low below (profile/single-eye one step lower). The detector is tuned on and matches the eyeballed turn stills; for the bulk corpus the counts are automated with spot checks of the contact sheets by eye (several of the flagged hires/imagine stills visibly lack the second green-side mark or have an extra one), so treat medium-confidence rows as "look at it".

Files: all_stills.csv, sheets/*.jpg, turn_faces_sheet.jpg, turn-NNN_face.png, tools/{bm.py,run.py,classify.py,final.py,overrides.json,results.jsonl}.
