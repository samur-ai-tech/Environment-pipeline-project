# BANK-ASTRA-003 — תוצאת בדיקה מוגבלת

## היקף ותוצאה

[measured: PREFLIGHT.json; LAUNCH.json; EXIT_CHECK.json] בדיקת native UI אחת בפרויקט Environmentpipeline, תחת lease של /root/bank_tier1_native_29. PID 13324 החל ב־2026-09-29 12:09:55 +03; LogExit Exiting ב־12:32:13; ב־12:32:35 לא נמצאו UnrealEditor/Houdini/HARS/hython. מפת העבודה /Engine/Maps/Templates/Template_Default, שמונה actors, All Saved בתחילה ובסוף. כל עורך נכס והעורך הראשי נסגרו ב־Alt+F4 ללא בקשת שמירה. לא נערכה שמירת Content או map.

[documented: ../BANK_ASTRA_003_BRIEF_2026-09-29.md] ההקצאה היא בדיקת מועמדי בנק בלבד. H0958 לא נפתח. לא בוצעו import/reimport, עריכת חומר, Houdini/HDA, cook/bake, BG1, Tier 1 build, M0/B1-C, Linear או שינוי קטלוג. לא נערך owner ledger; שחרור שייך למנהל.

## זהות וקריאות native UI

[measured: 01_H0907_identity__1.jpg; 12_H0013_identity__1.jpg; 27_H0051_identity__1.jpg; OBSERVATIONS.json] נתוני הקריאה מה־tooltip ומ־Static Mesh Editor; אינם בדיקת התנהגות collision.

| Candidate | Exact object path | LODs / displayed LOD | Triangles | Vertices | UV channels | Material slots | Collision primitives | Nanite |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| H0907 | /Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0907_Arab_x3_fbx.SM_H0907_Arab_x3_fbx | 1 / 0 (Auto) | 3302 | 4835 | 2 | 1 | 1 | false |
| H0013 | /Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0013_Building_04.SM_H0013_Building_04 | 1 / 0 (Auto) | 44241 | 45927 | 2 | 4 | 1 | false |
| H0051 | /Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0051_Garbagebin.SM_H0051_Garbagebin | 1 / 0 (Auto) | 5180 | 4776 | 2 | 1 | 1 | false |

[measured: identity screenshots] שלושתם מציגים CTF_UseSimpleAndComplex ו־BlockAll. H0907 Approx Size ב־tooltip הוא 1369 x 1369 x 1561, ובעורך 1369 x 1368 x 1560. H0051 מציג 29 x 34 x 74. יחידות לא סומנו בשדה שנקרא; לא הוסקו מידה מקומית מדויקת, מגע או גובה הפח לבדו. H0013 Approx Size אינו מתומלל כאן; המטרה המספרית היא UNKNOWN.

## חומרים: slot index, name, reference

[measured: native ordered Static Materials tooltip, Details Element indices, Browse selections, copied reference text files] שם ה־slot והחומר תואמים בזוגות ה־tooltip. Copy Reference נעשה ב־Ctrl+C על החומר שנבחר בעקבות Browse. חומר לא נפתח לעריכה.

| Candidate / Element | Slot name | Exact material object path | Receipt |
| --- | --- | --- | --- |
| H0907 / 0 | Arab_X3 | /Game/Project/Shared/Bank_ME_v3/Buildings/Arab_X3.Arab_X3 | H0907_MATERIAL_REFERENCE.txt |
| H0013 / 0 | Material_Building_04_1011 | /Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1011.Material_Building_04_1011 | H0013_MATERIAL_ELEMENT_0.txt |
| H0013 / 1 | Material_Building_04_1001 | /Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1001.Material_Building_04_1001 | H0013_MATERIAL_ELEMENT_1.txt |
| H0013 / 2 | Material_Building_04_1031 | /Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1031.Material_Building_04_1031 | H0013_MATERIAL_ELEMENT_2.txt |
| H0013 / 3 | Material_Building_04_1021 | /Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1021.Material_Building_04_1021 | H0013_MATERIAL_ELEMENT_3.txt |
| H0051 / 0 | Street_Props_Pack__003 | /Game/Project/Shared/Bank_ME_v3/StreetFurniture/Street_Props_Pack__003.Street_Props_Pack__003 | H0051_MATERIAL_REFERENCE.txt |

## H0907

[measured: 02–11 screenshots; OBSERVATIONS.json] מבנה שלם בעל כיפה, קשתות מחודדות, דלתות כחולות־אפורות וחלונות קטנים עם סבכה. Front ו־Back מציגים מערך פתחים דומה. Top מציג קונטור גג מצולע סביב כיפה עגולה. לא הוסקה משמעות תרבותית או שימוש בבניין.

[measured: 07_H0907_top__1.jpg; 09_H0907_dome_front__1.jpg] בכיפה נראים כתם בהיר עם גבול חד/מדורג מול אזור כהה יותר ופס גוון אופקי סביב בסיס הכיפה. זה גבול נראה בתצוגה, לא פגם מוכח. קיים slot אחד; מקור ההבדל ב־texture/UV/lighting לא הוכרע. צילום הכיפה הוא הגדלה מתונה, ולא תקריב UV או בדיקת texture binding. אין המלצת תיקון אוטומטי.

[measured: 03_H0907_floor_control_before__1.jpg; 05_H0907_floor_control_off__1.jpg; 04_H0907_front_floor_off__1.jpg; 08_H0907_bottom__1.jpg] Floor הוסתר דרך קיצור O שנראה בתפריט Preview Scene, עם checkbox מאומת לפני/אחרי. הרצפה הרחבה נעלמה; שפה תחתונה צרה נשארה. במבט Bottom נראה רקע דרך חלק גדול מהתחתית, בין קונטור מצולע לטבעת מרכזית, עם טלאים מלבניים. תיאור מוגבל: open underside in preview. אין כאן הוכחה למגע, אטימות או התאמה לפנים בניין. Floor הוחזר לפני סגירה (11).

## H0013

[measured: 14_H0013_floor_before__1.jpg; 16_H0013_floor_off_control__1.jpg; 15–21 screenshots] Floor הוסתר ואומת כ־unchecked. במבט התחתון נראים קווי מתאר וחלקים נפרדים; בחזית התחתונה נראים פתחים/דלתות ורצועות צרות דמויות סף. הרצפה הרחבה מהתצוגה אינה משמשת ראיה לריצוף משולב. אין להסיק מהצילומים היעדר מוחלט של גאומטריית בסיס או ריצוף בכל הנכס.

[measured: 18_H0013_front__1.jpg; 19_H0013_back__1.jpg; 20_H0013_top__1.jpg] במצלמת Front שורות רבות של חלונות ופתחים בקומת הקרקע. במצלמת Back קיר רחב כמעט ללא פתחים. בגג בלוקים מלבניים וצורות עגולות דמויות מכלים; התכנית מדורגת עם צד שקוע. שמות המצלמות אינם קביעה של חזית סמנטית.

[measured: 13; 22–25 screenshots and four reference receipts] ארבעת ה־slots תועדו בסדרם. [not run: mesh-local coordinate measurement] local bounds, signed contact, exact placement footprint, עומק הספים והגדרת צירים סמנטיים נשארו UNKNOWN. Floor הוחזר ו־All Saved תועד לפני סגירה (26).

## H0051

[measured: 28_H0051_floor_before__1.jpg; 30_H0051_floor_off_control__1.jpg; 29–34 screenshots] Floor הוסתר ואומת. פח בעל לוחות חומים ומסגרת מתכת בהירה, עם המשכי עמודי המסגרת מתחת לקורה התחתונה. Front/Left מציגים תומכים בולטים; Perspective מאפשר לראות את מבנה המסגרת. לא נמדדו נקודות המגע ולא הוסקו ארבעה מגעים מספריים מתוך ההיטל.

[measured: 31_H0051_front__1.jpg; 32_H0051_left__1.jpg; 33_H0051_top__1.jpg] בקבוק זקוף וצורות בקבוקים/פסולת נוספים בולטים מעל המסגרת העליונה ונכללים בנכס. גובה כל הנכס אינו גובה הפח לבדו. [measured: 34_H0051_bottom__1.jpg] תחתית חומה מרובעת נראית בתוך מסגרת אפורה; זו תצוגת underside ולא הוכחת watertightness או contact. חומר יחיד מאומת ב־35 ובקובץ reference. Floor הוחזר, Front ו־All Saved תועדו ב־36.

## סגירה והשוואת קבצים

[measured: FINAL_VALIDATION.json; CONTENT_BEFORE.json; CONTENT_AFTER.json] Content: 5991 קבצים לפני ואחרי; 0 added, 0 removed, 0 changed לפי relative path / size / UTC mtime. לא נטען SHA-256 לכל Content.

[measured: HASHES_BEFORE.json; HASHES_AFTER.json] כל 174 חתימות SHA-256 זהות: 172 קובצי Bank_ME_v3, canonical CSV ו־measurement EDITOR_OWNER.txt. הקטלוג BANK_CANDIDATE_INDEX_2026-09-28.csv נשאר 495985E2697C4BBBBE735E80184C5E73DA5B94A4444FEB5BAFDCBC6621ADEA42. מדידת ה־owner נותרה NONE; bank lease נותר של המפעיל עד בדיקת ושחרור המנהל.

[measured: SIDE_EFFECTS_BEFORE.json; SIDE_EFFECTS_AFTER.json; FINAL_VALIDATION.json] בתוך Saved: 4 added, 3 removed, 8 changed. נוספו CrashReportClient.ini ושלושה log backups; נמחקו שלושה log backups ישנים; השתנו AutoScreenshot.png, Autosaves/PackageRestoreData.json, שני קובצי Saved/Config/WindowsEditor, שני AutoSDKInfo, הלוג הפעיל ו־ShaderDebugInfo DDCKey. project Config עצמו ללא שינוי. [inference] דפוס זה תואם תופעות לוואי רגילות של session ורוטציית לוגים. קיום CrashReportClient.ini אינו הוכחת crash; SESSION_EDITOR.log מכיל shutdown רגיל. לא שוחזרו או נמחקו תופעות הלוואי.

## מגבלות ושלבים שלא הורצו

[not run] ערכי mesh-local עם יחידות, signed contact, footprint מספרי, bin-only height, collision behavior, performance/instances, semantic front/style/rights approval, Houdini connection, generation, scene save/reopen/regeneration וכל gate של qualification או acceptance. לא נעשתה עריכת חומר, isolation או wireframe; source atlas ו־texture binding לא נבדקו ב־session זה. גורם פס הגוון בכיפה UNKNOWN.

[measured: OBSERVATIONS.json] תפריטי תצוגה שנעלמו במעבר פעולה לא נרדפו. נעשה שימוש בפקדי Browse ובקיצורי תצוגה שנצפו בלבד. קיצורים בתחילת שחזור H0051 לא פעלו כאשר Details היה ממוקד; לחיצה ב־viewport אפשרה שחזור. שגיאת screenshotId מוקדמת נדחתה ללא פעולה. לא נוספה אוטומציה לעורך. העדות הראשונית 'No broad integrated paving' ביומן היא תיאור הפריים הנראה בלבד, ולא קביעה גאומטרית גורפת.

[documented: brief] qualified=no, technical_eligible=false, generation_enabled=false נשארים. הבדיקה השלימה תצוגות, זהות וחומרים מבוקשים; הנתונים המספריים שאינם זמינים נשארים UNKNOWN. המנהל אחראי ל־QA ולשחרור OWNER.

## אינדקס ראיות

OBSERVATIONS.json מכיל 38 רשומות עם זמן, חלון, טקסט נגישות וקובצי צילום מלאים. כל נתיב להלן יחסי לתיקייה זו; __0 הוא לרוב מסך מלא, __1 חלון הנכס ו־__2/3 tooltip/menu כשקיים.

- 00_startup: 00_startup__0.jpg
- 01_H0907_identity: 01_H0907_identity__0.jpg, 01_H0907_identity__1.jpg, 01_H0907_identity__2.jpg
- 02_H0907_front_floor_on: 02_H0907_front_floor_on__0.jpg, 02_H0907_front_floor_on__1.jpg, 02_H0907_front_floor_on__2.jpg
- 03_H0907_floor_control_before: 03_H0907_floor_control_before__0.jpg, 03_H0907_floor_control_before__1.jpg, 03_H0907_floor_control_before__2.jpg, 03_H0907_floor_control_before__3.jpg
- 04_H0907_front_floor_off: 04_H0907_front_floor_off__0.jpg, 04_H0907_front_floor_off__1.jpg
- 05_H0907_floor_control_off: 05_H0907_floor_control_off__0.jpg, 05_H0907_floor_control_off__1.jpg, 05_H0907_floor_control_off__2.jpg, 05_H0907_floor_control_off__3.jpg
- 06_H0907_back: 06_H0907_back__0.jpg, 06_H0907_back__1.jpg, 06_H0907_back__2.jpg
- 07_H0907_top: 07_H0907_top__0.jpg, 07_H0907_top__1.jpg, 07_H0907_top__2.jpg
- 08_H0907_bottom: 08_H0907_bottom__0.jpg, 08_H0907_bottom__1.jpg, 08_H0907_bottom__2.jpg
- 09_H0907_dome_front: 09_H0907_dome_front__0.jpg, 09_H0907_dome_front__1.jpg
- 10_H0907_material_browse: 10_H0907_material_browse__0.jpg, 10_H0907_material_browse__1.jpg, 10_H0907_material_browse__2.jpg
- 11_H0907_floor_restored: 11_H0907_floor_restored__0.jpg, 11_H0907_floor_restored__1.jpg
- 12_H0013_identity: 12_H0013_identity__0.jpg, 12_H0013_identity__1.jpg, 12_H0013_identity__2.jpg
- 13_H0013_ordered_slots: 13_H0013_ordered_slots__0.jpg, 13_H0013_ordered_slots__1.jpg, 13_H0013_ordered_slots__2.jpg
- 14_H0013_floor_before: 14_H0013_floor_before__0.jpg, 14_H0013_floor_before__1.jpg, 14_H0013_floor_before__2.jpg, 14_H0013_floor_before__3.jpg
- 15_H0013_lower_perspective_floor_off: 15_H0013_lower_perspective_floor_off__0.jpg, 15_H0013_lower_perspective_floor_off__1.jpg
- 16_H0013_floor_off_control: 16_H0013_floor_off_control__0.jpg, 16_H0013_floor_off_control__1.jpg, 16_H0013_floor_off_control__2.jpg, 16_H0013_floor_off_control__3.jpg
- 17_H0013_lower_front_close: 17_H0013_lower_front_close__0.jpg, 17_H0013_lower_front_close__1.jpg, 17_H0013_lower_front_close__2.jpg
- 18_H0013_front: 18_H0013_front__0.jpg, 18_H0013_front__1.jpg, 18_H0013_front__2.jpg
- 19_H0013_back: 19_H0013_back__0.jpg, 19_H0013_back__1.jpg, 19_H0013_back__2.jpg
- 20_H0013_top: 20_H0013_top__0.jpg, 20_H0013_top__1.jpg, 20_H0013_top__2.jpg
- 21_H0013_bottom: 21_H0013_bottom__0.jpg, 21_H0013_bottom__1.jpg, 21_H0013_bottom__2.jpg
- 22_H0013_element0_browse: 22_H0013_element0_browse__0.jpg, 22_H0013_element0_browse__1.jpg, 22_H0013_element0_browse__2.jpg
- 23_H0013_element1_browse: 23_H0013_element1_browse__0.jpg, 23_H0013_element1_browse__1.jpg, 23_H0013_element1_browse__2.jpg
- 24_H0013_element2_browse: 24_H0013_element2_browse__0.jpg, 24_H0013_element2_browse__1.jpg, 24_H0013_element2_browse__2.jpg
- 25_H0013_element3_browse: 25_H0013_element3_browse__0.jpg, 25_H0013_element3_browse__1.jpg, 25_H0013_element3_browse__2.jpg
- 26_H0013_floor_restored: 26_H0013_floor_restored__0.jpg, 26_H0013_floor_restored__1.jpg
- 27_H0051_identity: 27_H0051_identity__0.jpg, 27_H0051_identity__1.jpg, 27_H0051_identity__2.jpg
- 28_H0051_floor_before: 28_H0051_floor_before__0.jpg, 28_H0051_floor_before__1.jpg, 28_H0051_floor_before__2.jpg, 28_H0051_floor_before__3.jpg
- 29_H0051_perspective_floor_off: 29_H0051_perspective_floor_off__0.jpg, 29_H0051_perspective_floor_off__1.jpg
- 30_H0051_floor_off_control: 30_H0051_floor_off_control__0.jpg, 30_H0051_floor_off_control__1.jpg, 30_H0051_floor_off_control__2.jpg, 30_H0051_floor_off_control__3.jpg
- 31_H0051_front: 31_H0051_front__0.jpg, 31_H0051_front__1.jpg, 31_H0051_front__2.jpg
- 32_H0051_left: 32_H0051_left__0.jpg, 32_H0051_left__1.jpg, 32_H0051_left__2.jpg
- 33_H0051_top: 33_H0051_top__0.jpg, 33_H0051_top__1.jpg, 33_H0051_top__2.jpg
- 34_H0051_bottom: 34_H0051_bottom__0.jpg, 34_H0051_bottom__1.jpg, 34_H0051_bottom__2.jpg
- 35_H0051_material_browse: 35_H0051_material_browse__0.jpg, 35_H0051_material_browse__1.jpg, 35_H0051_material_browse__2.jpg
- 36_H0051_floor_restored: 36_H0051_floor_restored__0.jpg, 36_H0051_floor_restored__1.jpg
- 37_editor_before_close: 37_editor_before_close__0.jpg
