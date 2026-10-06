# BANK-ASTRA-001 — הכנת תת־קבוצה ומדידות

תאריך: 2026-09-29. Owner: Astra `01a0e820-c6d4-7702-8e7b-55fd20f9b020`.

**Preparation-time status:** the packet was prepared before an editor lease existed; no asset was qualified. **Authorized window:** the manager subsequently recorded BANK-ASTRA-001 for this operator from `2026-09-29T02:20:17.3257739+03:00` through `2026-09-29T03:05:17.3257739+03:00` [documented: `../EDITOR_OWNER.txt`, entry dated 02:20:17]. **Final status:** bounded inspection completed, Unreal closed without saving at 02:43:37, and the manager recorded OWNER=NONE at 02:45:08.9357886 +03. See `BANK_ASTRA_001_RESULT.md` and `LIVE_RELEASE_CHECK.json`. No asset was qualified. מנהל הבנק `01a0e7e2-2aac-7a63-a913-e58b1f3714a2` הוא בעל הקטלוג. כתיבה מוגבלת לתיקייה הזאת; Run01/Run02 והקטלוג נשמרים.

**Corrections after inspection:** the broad gridded platform around H0013 is preview scenery; the earlier integral-paving interpretation is withdrawn. H0958's imported alpha and exact Base Color texture binding are now measured, while the Opaque material leaves alpha disconnected. Detailed historical metrics and the proposed click list below are preparation records; the result receipt states what actually ran and what remains unknown.

## מסקנה ותת־קבוצה מינימלית מוצעת

[inference] הזוג המצומצם להכנת מדידת whole-instance הוא **H0013 + H0051**: בניין שלם ופריט רחוב, ללא החלפת מקור או תיקון. **H0015** נשמר כחלופת מגורים מעל מסחר בעלת מעטפת וגובה שונים. זו תת־קבוצת מועמדים למדידה, לא תת־קבוצה qualified ולא Tier 1 מלא.

[documented: CONTRACT.md §6.1] טיוטת Tier 1 מציינת H0907 ו־H0013, H0051 ו־H0958, בנוסף לקרקע, צומת ו־blockout. לכן חמש שורות ההכנה כוללות גם H0907 ו־H0958. H0015 אינו מחליף נכס חוזה ללא שינוי מפורש. BG1 הוא בדיקת מודולים פתוחה נפרדת; אין להמציא שהוא תנאי הכרחי למקטע שמוגדר בבניינים שלמים.

[documented: Run02/COMBINED_NATIVE_REVIEW.json] **אין צמחייה מוכשרת או מועמדת ללא כשל חומר ידוע מתוך שלושת נכסי הצמחייה ב־Bank_ME_v3**: H0636, H0647 ו־H0958 מציגים כשלי כרטיסי עלווה/חומר. Palms_Pack_01 אינו בתוך תחום אישור הזכויות של 32 נכסי v3, ואינו מוחלף אוטומטית במקום H0958.

[measured: H0958_SOURCE_ALPHA_READOUT.json] קובץ מקור העלים של H0958 הוא RGBA, בגודל 322×1024. נמצאו 223,817 פיקסלים עם A=0 ו־105,911 עם A=255, ללא ערכי ביניים. העותק בתיקיית Textures זהה ב־SHA-256. ערוץ alpha קיים; התאמתו למסכה המיועדת והישרדותו בטקסטורה המיובאת עדיין לא הוכחו. הגרף האטום מתועד ב־Run02; אין כאן שינוי או תיקון.

## תור ותוצאות שערים

| סדר | ID קצר | תפקיד מוצע | תפקיד בתור | שער חומר/תפקיד | מצב כולל |
|---|---|---|---|---|---|
| 1 | H0013 | בניין מגורים גבוה שלם; המשטח המרושת הוא רצפת התצוגה | בניין חוזה; מעטפת המודל ונקודות התמיכה עדיין דורשות מדידה | UNKNOWN: preview תקין חלקית; מגע, חזית ו־footprint חסרים | candidate / unqualified |
| 2 | H0015 | בניין מגורים מעל מסחר | חלופה מוצעת; לבדוק זיגוג ומרפסות | UNKNOWN: זיגוג מנומר ועלות לא נבדקה | candidate / unqualified |
| 3 | H0051 | פח רחוב עם בקבוקים/פסולת מובנים | prop חוזה; נקודות תמיכה וכיוון שימוש | UNKNOWN: detail/contact חסרים | candidate / unqualified |
| 4 | H0958 | דקל, מין/תקופה לא מאומתים | אבחון alpha ותלות בלבד | FAIL: כרטיסי עלים אטומים; source alpha קיים | HOLD / unqualified |
| 5 | H0907 | מבנה כיפה מיוחד/ביתן | חוזה; prior receipt בלבד במשימה הזאת | UNKNOWN: התאמה מקומית וגבולות גוון בכיפה | reserve / unqualified |

לכל החמישה: PASS רק לטעינה קודמת של הנכס ולרישום אישור הבעלים להכשרה טכנית. Qualified, connected, generated, scene visually verified, accepted נשארים false. ערכי allowed_zones בטבלה המפורטת הם הצעות, לא רשימת היתר פעילה.

## שורות מדויקות — מצב מדידה

### H0013

- asset_id / variant_id: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0013_Building_04` (ללא שינוי).
- Unreal object: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0013_Building_04.SM_H0013_Building_04`.
- קובץ נוכחי: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0013_Building_04.uasset`. SHA-256: `e5bb8f2ca2cf7ac473fa479251725933123a31f9f9d41d775eb11e675a039da6`.
- תפקיד `[inference]`: `tall_residential_whole_building`; representation מוצע `whole_instance`.
- אזורים מוצעים בלבד: `["residential_parcel_matching_full_base_envelope"]`; allowed_zones מאושר: UNKNOWN.
- מצב נצפה: weathered. The earlier integral-paving interpretation is withdrawn: separate section isolation confirms the broad grid platform is preview scenery [measured: LIVE observations 28–29].
- חומר: No default/checkerboard appearance in inspected views; four loaded materials. Close surface, seam and underside QA incomplete.
- `[documented: ME/IMPORT_RESULTS_v3.json]` Size cm: `[2889.69,2130.93,4868.35]`; local bounds min: `{"x":-1273.8673095703125,"y":-1081.9207763671875,"z":-0.3545195758342743}`; max: `{"x":1615.8203125,"y":1049.0091552734375,"z":4868}`. אלו מדידות יבוא קודמות, לא מדידה חיה חדשה.
- אותו מקור: reported pivot-to-bottom-centre `[-170.98,16.46,0.35]`. **אין להעביר ערך זה ל־signed contact vector**: נקודת התמיכה, הסימן ופעולת הטרנספורמציה לא אומתו.
- `[documented: native receipts]` LOD0 `44241` triangles, `45927` vertices, UV channels `2`, material slots `4`, collision primitives `1`, Nanite `unchecked`. Import metadata מדווח LOD count `1`. collision behavior/LOD performance: NOT RUN.
- חסר: exact local bounds verification אם נגיש ב־UI; signed contact/support points, semantic front/up, scale limits, physical size reference, collision behavior, scene performance, מקומיות/תקופה ו־Houdini. אין למלא UNKNOWN לפי גודל UI או שם הנכס.
- זכויות `[documented: LICENSE_PROVENANCE.md]`: אישור הבעלים להכשרה טכנית של 32 נכסי v3; ללא הרחבת זכויות הפצה/ייחוס או חבילות אחרות.

| slot מתועד | package מתועד | class מתועד | מצב תלות |
|---|---|---|---|
| Material_Building_04_1011 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1011` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |
| Material_Building_04_1001 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1001` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |
| Material_Building_04_1031 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1031` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |
| Material_Building_04_1021 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1021` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |

נתיבי texture מדויקים, hashes של חבילות החומר וראיות prior לכל שורה: `BANK_ASTRA_001_CANDIDATES.json`.

### H0015

- asset_id / variant_id: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0015_Building_02` (ללא שינוי).
- Unreal object: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0015_Building_02.SM_H0015_Building_02`.
- קובץ נוכחי: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0015_Building_02.uasset`. SHA-256: `106253b92e6b9c4c7a3cbbca9ee6baca337449d8957d3e8cbfef5779096655d2`.
- תפקיד `[inference]`: `residential_over_shops_whole_building`; representation מוצע `whole_instance`.
- אזורים מוצעים בלבד: `["mixed_use_parcel_street_frontage"]`; allowed_zones מאושר: UNKNOWN.
- מצב נצפה: weathered; blue glazing mottled.
- חומר: Textured facade present; blue glazing has conspicuous mottling. Compare close view before approval.
- `[documented: ME/IMPORT_RESULTS_v3.json]` Size cm: `[2034.02,1170.84,2417.33]`; local bounds min: `{"x":-1299.954345703125,"y":-563.1273193359375,"z":0.09817590564489365}`; max: `{"x":734.0643920898438,"y":607.7086181640625,"z":2417.42529296875}`. אלו מדידות יבוא קודמות, לא מדידה חיה חדשה.
- אותו מקור: reported pivot-to-bottom-centre `[282.94,-22.29,-0.1]`. **אין להעביר ערך זה ל־signed contact vector**: נקודת התמיכה, הסימן ופעולת הטרנספורמציה לא אומתו.
- `[documented: native receipts]` LOD0 `201057` triangles, `211808` vertices, UV channels `2`, material slots `4`, collision primitives `1`, Nanite `unchecked`. Import metadata מדווח LOD count `1`. collision behavior/LOD performance: NOT RUN.
- חסר: exact local bounds verification אם נגיש ב־UI; signed contact/support points, semantic front/up, scale limits, physical size reference, collision behavior, scene performance, מקומיות/תקופה ו־Houdini. אין למלא UNKNOWN לפי גודל UI או שם הנכס.
- זכויות `[documented: LICENSE_PROVENANCE.md]`: אישור הבעלים להכשרה טכנית של 32 נכסי v3; ללא הרחבת זכויות הפצה/ייחוס או חבילות אחרות.

| slot מתועד | package מתועד | class מתועד | מצב תלות |
|---|---|---|---|
| Building_02_1003 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Building_02_1003` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |
| Building_02_1004 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Building_02_1004` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |
| Building_02_1001 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Building_02_1001` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |
| Building_02_1002 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Building_02_1002` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |

נתיבי texture מדויקים, hashes של חבילות החומר וראיות prior לכל שורה: `BANK_ASTRA_001_CANDIDATES.json`.

### H0051

- asset_id / variant_id: `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0051_Garbagebin` (ללא שינוי).
- Unreal object: `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0051_Garbagebin.SM_H0051_Garbagebin`.
- קובץ נוכחי: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\StreetFurniture\SM_H0051_Garbagebin.uasset`. SHA-256: `1b1ca536131e7ae3d5616f887b29277ee6a29829d350d6d497b1043b44fc419d`.
- תפקיד `[inference]`: `pedestrian_waste_bin_with_attached_litter`; representation מוצע `compound_instance`.
- אזורים מוצעים בלבד: `["pedestrian_service_edge_outside_clear_walkway"]`; allowed_zones מאושר: UNKNOWN.
- מצב נצפה: littered; bottles integral.
- חומר: Slats/frame/bottles visible; close surface and ground-support QA incomplete. Current material path must distinguish StreetFurniture from same-name Props material.
- `[documented: ME/IMPORT_RESULTS_v3.json]` Size cm: `[29.4,34.43,74.4]`; local bounds min: `{"x":-12.837084770202637,"y":-17.898235321044922,"z":3.5086711136500526e-07}`; max: `{"x":16.559925079345703,"y":16.53656768798828,"z":74.40184783935547}`. אלו מדידות יבוא קודמות, לא מדידה חיה חדשה.
- אותו מקור: reported pivot-to-bottom-centre `[-1.86,0.68,-0.0]`. **אין להעביר ערך זה ל־signed contact vector**: נקודת התמיכה, הסימן ופעולת הטרנספורמציה לא אומתו.
- `[documented: native receipts]` LOD0 `5180` triangles, `4776` vertices, UV channels `2`, material slots `1`, collision primitives `1`, Nanite `unchecked`. Import metadata מדווח LOD count `1`. collision behavior/LOD performance: NOT RUN.
- חסר: exact local bounds verification אם נגיש ב־UI; signed contact/support points, semantic front/up, scale limits, physical size reference, collision behavior, scene performance, מקומיות/תקופה ו־Houdini. אין למלא UNKNOWN לפי גודל UI או שם הנכס.
- זכויות `[documented: LICENSE_PROVENANCE.md]`: אישור הבעלים להכשרה טכנית של 32 נכסי v3; ללא הרחבת זכויות הפצה/ייחוס או חבילות אחרות.

| slot מתועד | package מתועד | class מתועד | מצב תלות |
|---|---|---|---|
| Street Props Pack _003 | `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/Street_Props_Pack__003` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |

נתיבי texture מדויקים, hashes של חבילות החומר וראיות prior לכל שורה: `BANK_ASTRA_001_CANDIDATES.json`.

### H0958

- asset_id / variant_id: `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0958_CoconutPalm` (ללא שינוי).
- Unreal object: `/Game/Project/Shared/Bank_ME_v3/Vegetation/SM_H0958_CoconutPalm.SM_H0958_CoconutPalm`.
- קובץ נוכחי: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Vegetation\SM_H0958_CoconutPalm.uasset`. SHA-256: `e9575502d9e03f75537e2edcd02d22f444920aee7aa4ab1e48765752168bc3e6`.
- תפקיד `[inference]`: `palm_candidate_species_unverified`; representation מוצע `whole_instance`.
- אזורים מוצעים בלבד: `["planting_zone_after_species_and_crown_clearance_validation"]`; allowed_zones מאושר: UNKNOWN.
- מצב נצפה: opaque_foliage_card_defect; biological condition unknown.
- חומר: HOLD: prior visible opaque-card defect. Imported alpha and exact Base Color/Normal dependencies were measured in this run; Original_Submesh_1 remains Opaque/Default Lit, Two Sided off, with alpha disconnected [measured: LIVE observations 21–27]. No repair, UV-mask surface proof or new mesh-slot binding check occurred.
- `[documented: ME/IMPORT_RESULTS_v3.json]` Size cm: `[605.24,612.81,870.63]`; local bounds min: `{"x":-168.54640197753906,"y":-367.2211608886719,"z":-4.231946604704717e-06}`; max: `{"x":436.6885986328125,"y":245.5916290283203,"z":870.6278686523438}`. אלו מדידות יבוא קודמות, לא מדידה חיה חדשה.
- אותו מקור: reported pivot-to-bottom-centre `[-134.07,60.81,0.0]`. **אין להעביר ערך זה ל־signed contact vector**: נקודת התמיכה, הסימן ופעולת הטרנספורמציה לא אומתו.
- `[documented: native receipts]` LOD0 `4160` triangles, `3326` vertices, UV channels `2`, material slots `2`, collision primitives `1`, Nanite `False`. Import metadata מדווח LOD count `1`. collision behavior/LOD performance: NOT RUN.
- חסר: exact local bounds verification אם נגיש ב־UI; signed contact/support points, semantic front/up, scale limits, physical size reference, collision behavior, scene performance, מקומיות/תקופה ו־Houdini. אין למלא UNKNOWN לפי גודל UI או שם הנכס.
- זכויות `[documented: LICENSE_PROVENANCE.md]`: אישור הבעלים להכשרה טכנית של 32 נכסי v3; ללא הרחבת זכויות הפצה/ייחוס או חבילות אחרות.

| slot מתועד | package מתועד | class מתועד | מצב תלות |
|---|---|---|---|
| Original_Submesh_0 | `/Game/Project/Shared/Bank_ME_v3/Vegetation/Original_Submesh_0` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |
| Original_Submesh_1 | `/Game/Project/Shared/Bank_ME_v3/Vegetation/Original_Submesh_1` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |

נתיבי texture מדויקים, hashes של חבילות החומר וראיות prior לכל שורה: `BANK_ASTRA_001_CANDIDATES.json`.

### H0907

- asset_id / variant_id: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0907_Arab_x3_fbx` (ללא שינוי).
- Unreal object: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0907_Arab_x3_fbx.SM_H0907_Arab_x3_fbx`.
- קובץ נוכחי: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0907_Arab_x3_fbx.uasset`. SHA-256: `3c1726f412f92ac187a66e0c040c70ece42423527d1060c4d6ac5c57aff289bc`.
- תפקיד `[inference]`: `domed_landmark_pavilion`; representation מוצע `whole_instance`.
- אזורים מוצעים בלבד: `["exact_local_landmark_match_only"]`; allowed_zones מאושר: UNKNOWN.
- מצב נצפה: weathered; dome tone boundaries.
- חומר: Textured domed structure present; visible tone/patch boundaries on dome need intent/source review. Not typical residential architecture.
- `[documented: ME/IMPORT_RESULTS_v3.json]` Size cm: `[1369.04,1368.74,1560.66]`; local bounds min: `{"x":-680.353271484375,"y":-700.4720458984375,"z":0.6762058734893799}`; max: `{"x":688.6864013671875,"y":668.2713623046875,"z":1561.33740234375}`. אלו מדידות יבוא קודמות, לא מדידה חיה חדשה.
- אותו מקור: reported pivot-to-bottom-centre `[-4.17,16.1,-0.68]`. **אין להעביר ערך זה ל־signed contact vector**: נקודת התמיכה, הסימן ופעולת הטרנספורמציה לא אומתו.
- `[documented: native receipts]` LOD0 `3302` triangles, `4835` vertices, UV channels `2`, material slots `1`, collision primitives `1`, Nanite `unchecked`. Import metadata מדווח LOD count `1`. collision behavior/LOD performance: NOT RUN.
- חסר: exact local bounds verification אם נגיש ב־UI; signed contact/support points, semantic front/up, scale limits, physical size reference, collision behavior, scene performance, מקומיות/תקופה ו־Houdini. אין למלא UNKNOWN לפי גודל UI או שם הנכס.
- זכויות `[documented: LICENSE_PROVENANCE.md]`: אישור הבעלים להכשרה טכנית של 32 נכסי v3; ללא הרחבת זכויות הפצה/ייחוס או חבילות אחרות.

| slot מתועד | package מתועד | class מתועד | מצב תלות |
|---|---|---|---|
| Arab_X3 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Arab_X3` | Material | קובץ קיים; binding נוכחי לא נבדק מחדש |

נתיבי texture מדויקים, hashes של חבילות החומר וראיות prior לכל שורה: `BANK_ASTRA_001_CANDIDATES.json`.

## סדר UI מוצע לאחר lease מפורש בלבד

החלון מוגבל ל־45 דקות מתחילת lease, כולל סגירה ורישום שחרור. אין לפתוח HDA/map עבודה. אין Scene placement, שינוי Asset, Apply/Save/Compile/Import, cook/bake, תיקון, Houdini או Linear.

1. **W0** — מנהל הבנק מתאם עם integration ומוסר lease כתוב עם BANK-ASTRA-001, owner, scope, PID קיים אם רלוונטי, map, זמני התחלה/סיום ודרך release. לפני קלט: בדיקה חוזרת של בעלים/מפעילים ותהליכים, מצב dirty ובסיס Content. אם יש סתירה, עוצרים. רישום בעלות רק בתיקיית הבנק לפי הליך המנהל; אין לשנות מדידה.
2. **W1** — רק לאחר lease תקף: לפתוח את הפרויקט על `/Engine/Maps/Templates/Template_Default` באמצעות PowerShell/Windows; לרשום PID בפועל (לא להמציא מראש). לוודא map ו־All Saved, לא לבחור Resume/Cook/Session. אם עורך קיים — להשתמש בו רק במסגרת handover מפורש, לא לנחש בעלות.
3. **A1 H0051, יעד כ־7 דקות** — `Ctrl+P`, חיפוש exact name + `Path=/Game/Project/Shared/Bank_ME_v3/StreetFurniture/`. לפתוח את התוצאה המדויקת בלבד. ללחוץ viewport ואז `F`; לצלם full ו־close של תחתית/מסגרת/בקבוקים. להשתמש ב־Perspective ובמצבי Front/Back/Top דרך תפריט המצלמה ולצלם axis gizmo; אין לזהות Front camera עם semantic front. לקרוא collision view בלבד אם זמינה, לא Generate/Add/Remove. לקרוא slot/path באמצעות Browse/פתיחת material בלבד; לבדוק שמדובר ב־StreetFurniture ולא Props.
4. **A2 H0013, יעד כ־10 דקות** — exact path לעיל. full facade, opposite, Top/base views; לזהות כל פאה/אדן/ריצוף שמרחיב footprint. לקרוא ארבעה slots, הנתונים הגאומטריים, Nanite/LOD count/collision complexity כפי שמוצגים. לפתוח Details חיפוש bounds רק לקריאה: extension fields אינם actual bounds. אם UI לא נותן numeric local min/max או תמיכות, לתעד UNKNOWN + צילום היכולת החסרה. אין להפיק signed contact מצילום או מגבול תחתון.
5. **A3 H0015, יעד כ־9 דקות** — exact path לעיל. לצלם frontage shops/balconies והזיגוג מקרוב; להשוות צדדים/גג ותמיכה. לזהות ארבעה material paths באופן מדויק ולקרוא LOD/collision. לא לשנות לחומר אחר לצורך השוואה. H0015 נשאר חלופה מוצעת; אין לבחור אותו במקום H0013/H0907 בחוזה.
6. **A4 H0958 dependency, יעד כ־9 דקות** — אין צורך לחזור על mesh preview שכבר מוכיח cards. לפתוח לקריאה את `/Game/Project/Shared/Bank_ME_v3/Vegetation/Original_Submesh_1`; לזהות texture sample actual object path. לפתוח את הטקסטורה המיובאת `coconut_palm_leaf_3f6407d492f8_albedo_cdcdc62b95fb29` ולקרוא Texture2D class, source filename אם מוצג, dimensions, compression/alpha discard, ולצפות ב־A channel באמצעות viewer display בלבד. אין לשנות checkbox של הגדרות asset או לחבר nodes. `[not run]` אם alpha display לא נגיש. מקור PNG כבר נמדד; source shader ו־mask correspondence עדיין חסרים.
7. **W2, יתרת זמן כ־10 דקות** — לשחזר display toggles ככל שנדרש, לוודא שאין dirty assets, לסגור בלי שמירה לפי מצב ה־UI; אם יש dirty שלא נוצר מתצוגה צפויה, לעצור ולתעד בלי save/discard אוטומטי. לתעד process exit ושחרור בעלות, inventory/hash preservation ו־receipt לכל סעיף. אין לפתוח H0907 או משפחות נוספות בלי הרחבת המשימה מהמתאם.

המספרים לעיל הם יעדי זמן, לא זמן ביצוע שנמדד. אם נגמר הזמן, לסגור/לשחרר ולדווח partial עם בדיוק מה שלא רץ.

## תנאי סגירת מדידה ומגבלות אמיתיות

- טעינה/חומר: exact class/path עם צילום, material slots/dependencies מלאים, שני מבטים מועילים לבעיה. Close-up נקי אינו קבלה לסצנה.
- גאומטריה: bounds מקוריים מתועדים קיימים; צריך לאמת את מסגרתם ונקודות התמיכה לפני catalog-to-HDA contact. Numeric bounds, contact וטרנספורמציית הצבה עלולים להיות מעבר למה שניתן להוכיח ב־asset preview ללא placement. במקרה זה report UNKNOWN והצע שער מדידה נפרד, לא script/scene לא מורשים.
- גנרציה: למדידת מגע מאוחרת חייבים להגדיר אם וקטור contact הוא נקודה במרחב local או translation correction, ואת פעולת rotation/scale. להשוות support points לקרקע לפי דרישת החוזה; טרם נבחרה שיטת המדידה בפועל.
- H0958: source-alpha PASS אינו surface PASS. נדרש actual imported alpha/binding, מקור shader ולבסוף תיקון מורשה עם variant identity וקישור למקור. המשימה הזאת אינה מתירה תיקון.
- Tier 1 נשאר חסום ע״י החוזה DRAFT ושערי המסלול, ובנוסף אין צמחייה תקינה מאושרת בתוך v3. לא מריצים BG1/Tier 1 ולא ממציאים qualified subset.

## בעלות ורצף

At preparation time this packet awaited an explicit lease; historical OWNER=NONE was not authorization. The manager subsequently granted the bounded window recorded above. Preflight, native inspection and no-save exit are now recorded in this folder. The manager released the lease to OWNER=NONE at 02:45:08.9357886 +03. The operator did not write the owner ledger or canonical catalog; any further editor action needs a new assignment and lease.
