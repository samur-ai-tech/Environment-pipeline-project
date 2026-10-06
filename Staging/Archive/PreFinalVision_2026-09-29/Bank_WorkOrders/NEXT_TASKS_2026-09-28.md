# משימות ההמשך — ModelBank

תאריך: 2026-09-28. מפעיל חדש: Astra, thread 01a0e820-c6d4-7702-8e7b-55fd20f9b020.

## LOCK — בדיקה חדשה בכל סבב

החסימה של PID 18000 הוסרה לפני Native_Visual_Run_01. נלקחה בעלות ב־17:11:28+03:00, PID 33844 נסגר ללא שמירה, והבעלות שוחררה ב־17:56:29+03:00. [measured: Native_Visual_Run_01/preflight.json; release_check.json]

לפני חזרה לעורך יש לבדוק מחדש: סיום המדידה, רשומת OWNER=NONE העדכנית, שאין מפעיל פעיל או תהליך סותר, ולרשום רכישה ושחרור תחת ModelBank בלבד. אין להשתמש בבדיקה הישנה כהוכחה לנעילה חדשה. אין לשנות קובצי מדידה.

## BANK-NATIVE — בדיקת נכסים קיימים, לאחר פתרון LOCK

בדיקה זו כבר כלולה בהרשאת Aviv; אין לבקש אישור מחדש לבדיקה המוגבלת הזאת. אין יבוא, שינוי Content, שמירת מפה, cook, bake או יצירת מופעים. אם נדרשת פעולה החורגת מצפייה ב־asset editor, מתעדים not run ומשימה נפרדת. אין לפתוח מפה שעלולה להפעיל HDA או session. אין ללחוץ Apply/Save/Compile או לשנות הגדרות נכס.

### אצווה ראשונה — תשעה נכסים: נצפו ב־Native_Visual_Run_01

כל תשעת הנתיבים הבאים נפתחו כעת בתצוגות נכס, בחיפוש Name ו־Path מדויקים. זו אינה הכשרה לתפקיד. ראיות: Native_Visual_Run_01/native_receipts.json. טבלת התפקידים המקורית להלן היסטורית; functional_role המעודכן בקטלוג ודוח הצפייה קודמים לה.

| סדר | asset_id | Unreal object path | תפקיד מוצע |
|---|---|---|---|
| 1 | `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0907_Arab_x3_fbx` | `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0907_Arab_x3_fbx.SM_H0907_Arab_x3_fbx` | whole_building |
| 2 | `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0014_Building_01` | `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0014_Building_01.SM_H0014_Building_01` | whole_building |
| 3 | `current_ModularCourtyard__Meshes__SM_wall_windows_4x4_01` | `/Game/ModularCourtyard/Meshes/SM_wall_windows_4x4_01.SM_wall_windows_4x4_01` | window_bay |
| 4 | `current_ModularBuildingSet__Meshes__Store_fronts__store_front_shutters_4x1_a` | `/Game/ModularBuildingSet/Meshes/Store_fronts/store_front_shutters_4x1_a.store_front_shutters_4x1_a` | storefront_bay |
| 5 | `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0051_Garbagebin` | `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0051_Garbagebin.SM_H0051_Garbagebin` | street_waste_bin |
| 6 | `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0636_Acacia` | `/Game/Project/Shared/Bank_ME_v3/Vegetation/SM_H0636_Acacia.SM_H0636_Acacia` | tree_or_shrub |
| 7 | `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0082_Streetsign` | `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0082_Streetsign.SM_H0082_Streetsign` | sign_or_graphic |
| 8 | `current_StarterContent__Materials__M_Concrete_Poured` | `/Game/StarterContent/Materials/M_Concrete_Poured.M_Concrete_Poured` | sidewalk_surface |
| 9 | `current_FC_Coastal_Landscape__Landscape__M_Master_CL_Landscape` | `/Game/FC_Coastal_Landscape/Landscape/M_Master_CL_Landscape.M_Master_CL_Landscape` | ground_surface |

### המשך שיטתי בכל המשפחות — נותרו 907 רשומות נוכחיות ו־285 חיצוניות

`Native_Visual_Run_01/BANK_NATIVE_PENDING.csv` הוא התור המדויק לרשומות הנוכחיות, כולל IDs, source paths, Unreal object paths, תפקיד ומשפחה. 23 נכסים ב־12 משפחות נצפו חלקית; אין להרחיב ראיה של נציג לכל המשפחה. נוספה ראיה להפרדה בין Store_fronts לבין Store_fronts_interiors עבור intact_4x1_a.

מקור העבודה הוא BANK_CANDIDATE_INDEX_2026-09-28.csv המעודכן, FAMILY_REVIEW.csv ו־MEMBER_REVIEW.csv. כל 324 המשפחות נותרות בהיקף. השדה native_batch מפנה לתור המשפחות; REPRESENTATIVE_SUBSET_PROPOSED.csv הוא הצעה להשוואה ראשונית, לא מגבלת היקף.

1. להשוות Bank_ME_v3 לפי גובה/שימוש/מעטפת ומצב, כולל כל 32 הרשומות.
2. להשוות חלונות/דלתות/קירות/קצות גג של ModularCourtyard; צדדים, פינות ופנים מול חוץ של ModularBuildingSet.
3. להשוות B18/B55/B93 וחומר/מצב/קצה של ProceduralBuildingGenerator; לפתוח technical variant רק אם הוא עשוי לשנות בחירה או עלות.
4. להשלים את 11 הדקלים שטרם נצפו מתוך משפחת 16 הדקלים ב־Palms_Pack_01 (המשפחה כוללת green/dry/fallen), ואת צמחיית התחתית; לא לצמצם לשלוש הדגימות בלי ראיה. FoliageType אינו צורת עץ נוספת.
5. לבדוק חומרי FC_Coastal_Landscape ו־StarterContent ותלות פונקציות/instances; לא להציג material function כחומר מוכן.
6. להשלים Warehouse ורזרבות AssetsvilleTown/Stylized_Egypt/UtopianCity לפי תפקיד. Exclude הוא המלצת scope בלבד; לא מוחקים נכס.
7. MOUT_Arabian, ערכות CityBLD וארכיון Hergel/Terre: להמשיך רק בראיות מקור קיימות עד GO נפרד ליבוא.

לכל asset/family: צילום מזהה עם הנתיב ושני מבטים מועילים כשצריך; close variants באותה תאורה ופרספקטיבה; זהות class; חומר/מרקם, שקיפות, normals ו־UV שנראים; bounds ויחידות שהעורך מציג; pivot/front/up רק כשמוכחים; slots/dependencies; LOD/Nanite/collision ו־triangles לפי UI. לא משנים LOD או collision. אם אין מדידה, השדה נשאר ריק ומסומן not run.

שער BANK-NATIVE: לכל המלצה מזהים מדויקים, היקף ראיה, צילום או תיעוד מדד, הבדלים שנשמרו, ו־next gate. צפייה ב־asset editor מוכיחה רק את הנצפה שם; qualification, connected, generated ו־accepted אינם משתנים בעקבותיה בלבד. בסוף רושמים שחרור בעלות.


## ממצאים פעילים ושערי המשך מדויקים

1. **ACACIA-DIAGNOSE** — exact ID `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0636_Acacia`, path `/Game/Project/Shared/Bank_ME_v3/Vegetation/SM_H0636_Acacia.SM_H0636_Acacia`. במסגרת צפייה מורשית: לקרוא קשרי Material_28/40/41 והטקסטורות, domain/blend/two-sided/opacity; להשוות ל־ME/IMPORT_RESULTS_v3.json ולמקור billboard החסר. אין לשנות. אם נחוץ תיקון, להכין רשימת חומרים/טקסטורות מדויקת, מקור מורשה, hashes, אופן יבוא/שינוי ויעדים להוראת GO נפרדת. שער התוצאה: אותה צורה ללא לוחות אטומים בשתי זוויות, תלות מתועדת ובלי overwrite מקור.
2. **H0014-PERF** — `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0014_Building_01.SM_H0014_Building_01`: לשמור את המראה המעוטר ולא לפסול רק בגלל 2,476,576 משולשים. להכין בדיקת מרחקים/LOD ועלות מופע תחת GO נפרד אם היא דורשת מפה או יצירה. baseline ומדדי GPU/CPU/זיכרון צריכים להיות נפרדים ממספר המשולשים.
3. **SHOP-PAIR** — שני paths המדויקים ב־native_receipts.json תחת Store_fronts ו־Store_fronts_interiors עבור store_front_windows_intact_4x1_a. לשמר את שתי הגרסאות; לבדוק חריץ אנכי, חיבורי קצה, back-face, thickness ו־collision. הרכבה או תיקון רק במשימת ביצוע נפרדת. שער: תמונות הצדדים ותפרים עם קנה מידה, מגע ו־bounds מדודים.
4. **WINDOW-MODULES** — SM_wall_windows_4x4_01/open ו־B18/B55/B93 מתוך native_receipts.json: לבחור דרישות closed exterior מול through-opening לפני BG. למדוד module dimensions/pivot/axes/handedness ורשימת מחברים, בלי להסיק משם 3x3/4x4. BG1 נשאר not run ודורש חוזה מאושר ו־GO נפרד.
5. **PALM-COMPARE** — להשלים את ה־11 שבתור המשפחה, לשמור ירוק בוגר/צעיר, יבש ונפול בנפרד. LOD3 לא נבדק; לתעד בפועל מצב LOD לפני טענת מעבר. אין לשנות LOD assets או wind settings.
6. **SURFACE1** — M_Concrete_Poured ו־M_Master_CL_Landscape נצפו על כדור בלבד. להכין, אך לא להריץ, משטח בקנה מידה ידוע ותכנית layers/masks/tiling; שימוש Landscape או Houdini דורש GO נפרד.

## BANK-IMPORT — משימה עתידית, נדרש GO נפרד

[proposed] בסיס הבחירה המדויק הוא הרשומות source_scope=external מתוך REPRESENTATIVE_SUBSET_PROPOSED.csv, עם כל member paths ב־MEMBER_REVIEW.csv. לפני ביצוע, לקבע רשימה קטנה יותר רק לאחר בדיקת זכויות ותלויות, ולתעד source project/version, סוג קובץ, importer נתמך ויעד מפורש.

לנכסי Unreal: להשתמש ב־Migrate הנתמך מתוך פרויקט המקור ובדוח התלויות שלו. אין העתקת uasset ידנית. Migrate משמר מבנה package תחת Content; יש לבדוק מראש את כל יעדי הקבצים וההתנגשויות. שינוי מסלול package אינו נכלל באישור יבוא בלי החלטה מפורשת. ל־FBX/OBJ: לייבא רק דרך importer נתמך עם materials/textures וכללי cm/axis מתועדים. [proposed] יעד לבדיקה בלבד: /Game/Developers/USER/ModelBankReview/<Pack>/ עבור מקורות interchange; אינו יעד מאושר ואינו חל אוטומטית על Migrate. אין שינוי מקור או החלפת קבצים קיימים.

שער יבוא: manifest לפני/אחרי, זכויות לפי scope, hashes של המקורות, רשימת תלויות, 0 overwrite לא מאושר, exact object paths, טעינה וחומרים, יחידות ו־bounds, תמונות באותו קנה מידה. פתיחה מחדש ושמירה דורשות את משימת הביצוע הנפרדת ונתיבי שמירה מפורשים. היבוא לבדו אינו qualification.

## BANK-ROLE — בדיקות תפקיד עתידיות

[not run: INST1/BG1/SURFACE1] רק אחרי החלטות החוזה והוראות ביצוע נפרדות.

- Whole building/prop/vegetation: בדיקת unreal_instance, זהות/נתיב, base contact, front/up, footprint, clearance, variation, חומרים ו־performance. בניין שלם אינו מודול BG.
- Building module: בדיקת מחבר, רוחב/גובה/עומק, pivot, handedness, פינות וסגירת תפרים עם גאומטריית module. להגדיר רשימת חלקים מלאה ו־fallback לפני BG1; אין fallback שנבנה בסקירה הזו.
- Road/ground material: לבדוק units/tiling, layers, masks, גאומטריית המשטח, seams ונראות; mesh מדרכה אינו חומר ואינו מחליף את רשת Houdini.

שערי התפקיד יפרטו פרמטרים, map/output paths מפורשים, גרסאות/input hashes, counts/IDs, בדיקה חזותית של Aviv, save/reopen בתהליך חדש, recook ובשלב bake גם rebake עם replace וללא כפילויות, לפי CONTRACT המאושר בעת הביצוע. בשלב זה v0.6 עדיין DRAFT ולא מתבצעת אף בדיקה כזאת.

## RIGHTS — מסמכים חסרים

אישור הבעלים ל־32 נכסי Bank_ME_v3 נשמר ואינו נשאל שוב. נדרשים מסמכי מקור/רישיון וקישור לקבלה עבור Palms_Pack_01 והחבילות החיצוניות הנבחרות; תנאי השימוש לחבילות עם קבלות מתועדות; וזכויות מרקמים/המרות במקורות Hergel/Terre/SpeedTree. זיהוי listing אינו הוכחת entitlement. אין הרחבת אישור v3 ליתר הארכיון.
