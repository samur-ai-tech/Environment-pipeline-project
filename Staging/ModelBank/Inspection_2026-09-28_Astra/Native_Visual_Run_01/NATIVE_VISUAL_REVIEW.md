# GazaRimal — ממצאי צפייה בתוך Unreal, סבב 01

תאריך: 2026-09-28. מפעיל חדש: Astra, thread `01a0e820-c6d4-7702-8e7b-55fd20f9b020`.

**23 נכסים נפתחו ונצפו בפרויקט הנוכחי, מתוך 12 משפחות ושבע חבילות.** כל תשעת נכסי ASTRA_VISUAL_PREP ועוד 14 נבדקו. זהו סבב חלקי; 907 רשומות שכבר נמצאות בפרויקט ו־285 רשומות חיצוניות טרם נצפו כאן. כל 1,215 הרשומות נשארות בקטלוג.

[measured: preflight.json; release_check.json] לאחר שנמצא שאין תהליך עורך סותר, נלקחה בעלות ונפתח PID 33844 עם `/Engine/Maps/Templates/Template_Default`. נבדקו נכסים קיימים בלבד. העורך נסגר דרך הממשק ללא שמירה והבעלות שוחררה ב־17:56:29+03:00. אין תהליך Unreal/Houdini/HARS בסיום; קובץ בעלות המדידה נשאר באותו SHA-256. השוואת 5,989 קובצי Content לפני/אחרי לא מצאה הבדל בנתיבים, גודל או מועד כתיבה. זו השוואת מטא־דאטה, לא hash מלא של Content. לא נמצא קובץ מדידה עם מועד כתיבה מאוחר מרכישת הנעילה.

## גבולות הראיה

- `[measured]` להלן הוא מה שנראה בתצוגת הנכס או בלוח הנתונים, תחת התאורה המובנית. `[inference]` הוא תפקיד והתאמה מוצעים ל־GazaRimal.
- תצוגת נכס אינה הצבה בסצנה, חיבור Houdini, גנרציה, qualification או acceptance. `visually_verified` נשאר `no` עבור שער הסצנה/הפלט; השדה החדש `native_preview_state=observed_partial` מתעד צפייה אמיתית בפרויקט.
- המספרים הגאומטריים הם LOD0. Approx Size הועתק כמחרוזת ללא הנחת יחידות; שדות cm קיימים נשמרו. לא נמדדו contact offset, pivot או מיפוי front/up. Front/Back הם שמות מצלמה, לא כיוון סמנטי של חזית.
- מספר collision primitives אינו בדיקת התנגשות. לא בוצעו בדיקות LOD transition, runtime performance, Unity או Houdini. תפרי הרכבה ו־BG1 לא נבדקו.
- ב־Palm01 נצפה תפריט LOD0–3; ניסיון בחירת LOD3 השאיר Auto/LOD0. אין ראיה שנבדק LOD3. נראתה תנועה בין תמונות, אך לא נערך מבחן wind.
- הודעת Ray Tracing בזיכרון הופיעה לאחר סדרת תצוגות: 83.76 MiB מתוך 400 MiB ועבירת 20% מהתקציב. זו הודעת סשן, לא עלות מוכחת של נכס מסוים ולא benchmark.
- הקבצים הגולמיים כוללים מצבי טעינה, תפריטים וניסיונות שינוי זווית שלא הצליחו. שמות קבצים כגון `43_Palm01_LOD3` מתארים כוונה ואינם הוכחת תוצאה. `native_receipts.json` מגדיר את התצפיות התקפות; `native_evidence_manifest.json` קושר צילומים ו־hashes.

## ממצאים לפי נכס

### 1. SM_H0907_Arab_x3_fbx

ID: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0907_Arab_x3_fbx`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0907_Arab_x3_fbx.SM_H0907_Arab_x3_fbx`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0907_Arab_x3_fbx.uasset`

[measured] מבנה שלם בעל כיפה רחבה, דלתות כחולות־אפורות וקשתות מעוטרות. נראים גבולות גוון על הכיפה.

[inference] review: מבנה מיוחד או ביתן; השימוש המקומי המדויק אינו ידוע.

[measured] LOD0: **3,302 triangles**, 4,835 vertices; UV channels 2; material slots 1; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `1,369 x 1,368 x 1,560`.

זכויות: `owner_confirmed_for_technical_qualification`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_H0907_Arab_x3_fbx](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/06_H0907_whole__1.jpg)

### 2. SM_H0014_Building_01

ID: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0014_Building_01`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0014_Building_01.SM_H0014_Building_01`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0014_Building_01.uasset`

[measured] בניין שלם עם שלוש שורות מרפסות מעל קומת חנויות, תריסים ירוקים, קשתות, מזגנים וצלחות. נראים כתב ערבי וגרפיטי; הטקסט לא תומלל.

[inference] review: מגורים מעל מסחר במראה ותיק ומעוטר. 2,476,576 משולשים ב־LOD0 מחייבים בדיקת עלות, ללא סף פסילה אוטומטי.

[measured] LOD0: **2,476,576 triangles**, 2,775,920 vertices; UV channels 4; material slots 8; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `1,728 x 2,095 x 2,119`.

זכויות: `owner_confirmed_for_technical_qualification`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_H0014_Building_01](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/14_H0014_perspective__1.jpg)

### 3. SM_wall_windows_4x4_01

ID: `current_ModularCourtyard__Meshes__SM_wall_windows_4x4_01`

Unreal: `/Game/ModularCourtyard/Meshes/SM_wall_windows_4x4_01.SM_wall_windows_4x4_01`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ModularCourtyard\Meshes\SM_wall_windows_4x4_01.uasset`

[measured] קיר טיח אוכרה שחוק עם שני חלונות סגורים, אדנים וכתמי לבנים. הצד הנגדי הוא קיר אטום.

[inference] keep כמועמד למקטע חזית חיצוני סגור; אינו פתח שעובר דרך הקיר.

[measured] LOD0: **656 triangles**, 916 vertices; UV channels 2; material slots 4; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `54 x 400 x 400`.

זכויות: `acquisition_record_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_wall_windows_4x4_01](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/21_Courtyard_whole__1.jpg)

### 4. store_front_shutters_4x1_a

ID: `current_ModularBuildingSet__Meshes__Store_fronts__store_front_shutters_4x1_a`

Unreal: `/Game/ModularBuildingSet/Meshes/Store_fronts/store_front_shutters_4x1_a.store_front_shutters_4x1_a`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ModularBuildingSet\Meshes\Store_fronts\store_front_shutters_4x1_a.uasset`

[measured] תריס חנות מתכתי סגור ומנוקב, שטוח. לא נראה מצד Back לאחר מסגור.

[inference] keep כמועמד ל־inset עם קיר תומך; אינו דלת עצמאית או פתח פתוח.

[measured] LOD0: **16 triangles**, 32 vertices; UV channels 2; material slots 2; collision primitives 0; Nanite unchecked. Approx Size (יחידה לא מסומנת): `0 x 600 x 384`.

זכויות: `acquisition_record_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של store_front_shutters_4x1_a](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/24_Storefront_whole__1.jpg)

### 5. SM_H0051_Garbagebin

ID: `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0051_Garbagebin`

Unreal: `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0051_Garbagebin.SM_H0051_Garbagebin`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\StreetFurniture\SM_H0051_Garbagebin.uasset`

[measured] פח רחוב מחופה לוחות חומים במסגרת בהירה, עם בקבוקים ופסולת מובנים בחלק העליון.

[inference] review: וריאנט מלוכלך; לא לשכפל את אותם בקבוקים בכל הרחוב.

[measured] LOD0: **5,180 triangles**, 4,776 vertices; UV channels 2; material slots 1; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `29 x 34 x 74`.

זכויות: `owner_confirmed_for_technical_qualification`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_H0051_Garbagebin](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/28_Garbagebin__1.jpg)

### 6. SM_H0636_Acacia

ID: `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0636_Acacia`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Vegetation/SM_H0636_Acacia.SM_H0636_Acacia`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Vegetation\SM_H0636_Acacia.uasset`

[measured] לאחר טעינה נותרו לוחות לבנים אטומים וכתמי עלווה שחורים וזוויתיים.

[inference] review חסום לשימוש בשל כשל חזותי. הסיבה בחומר או בשקיפות היא הסקה בלבד; לא בוצע תיקון.

[measured] LOD0: **4,352 triangles**, 2,562 vertices; UV channels 2; material slots 3; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `552 x 454 x 481`.

זכויות: `owner_confirmed_for_technical_qualification`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_H0636_Acacia](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/32_Acacia_whole__1.jpg)

### 7. SM_H0082_Streetsign

ID: `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0082_Streetsign`

Unreal: `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0082_Streetsign.SM_H0082_Streetsign`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\StreetFurniture\SM_H0082_Streetsign.uasset`

[measured] שלט מתומן אדום עם דמות אדם לבנה על עמוד; אינו שלט שם רחוב.

[inference] review עד לביסוס משמעות והתאמה מקומית של הסמל.

[measured] LOD0: **420 triangles**, 569 vertices; UV channels 2; material slots 1; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `40 x 7 x 122`.

זכויות: `owner_confirmed_for_technical_qualification`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_H0082_Streetsign](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/34_Streetsign_loaded__1.jpg)

### 8. M_Concrete_Poured

ID: `current_StarterContent__Materials__M_Concrete_Poured`

Unreal: `/Game/StarterContent/Materials/M_Concrete_Poured.M_Concrete_Poured`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\StarterContent\Materials\M_Concrete_Poured.uasset`

[measured] בטון אפור בהיר מחוספס נראה על כדור התצוגה. חיבורי BaseColor, Roughness ו־Normal נראים בגרף.

[inference] keep כמועמד לבטון כללי; tiling וגוון על משטח אמיתי טרם נבדקו.

[measured] Surface; Opaque; Default Lit; Two Sided unchecked. [not run] Scale/tiling, layers, surface and runtime test.

זכויות: `unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של M_Concrete_Poured](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/36_Concrete_preview__1.jpg)

### 9. M_Master_CL_Landscape

ID: `current_FC_Coastal_Landscape__Landscape__M_Master_CL_Landscape`

Unreal: `/Game/FC_Coastal_Landscape/Landscape/M_Master_CL_Landscape.M_Master_CL_Landscape`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\FC_Coastal_Landscape\Landscape\M_Master_CL_Landscape.uasset`

[measured] משטח מנומר חום־אפור כהה נראה על כדור. הגרף משתמש ב־Material Attributes; מתג RuntimeVirtualTextureEnable? מוצג False.

[inference] review כמערכת חומר; אין ראיה למיזוג שכבות Landscape או למסכות Houdini.

[measured] Surface; Opaque; Default Lit; Use Material Attributes checked; Two Sided unchecked. [not run] Scale/tiling, layers, surface and runtime test.

זכויות: `acquisition_record_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של M_Master_CL_Landscape](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/39_Coastal_loaded__1.jpg)

### 10. SM_Palm_01_01_G

ID: `current_Palms_Pack_01__Meshes__SM_Palm_01_01_G`

Unreal: `/Game/Palms_Pack_01/Meshes/SM_Palm_01_01_G.SM_Palm_01_01_G`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Palms_Pack_01\Meshes\SM_Palm_01_01_G.uasset`

[measured] דקל ירוק גבוה, גזע מעט נוטה וכתר מניפה עם חצאית עלים יבשים ארוכה. חיתוכי העלים נראים תקינים בתצוגה.

[inference] keep כמועמד לצורה בוגרת; התאמת המין ל־Rimal לא הוכחה.

[measured] LOD0: **19,293 triangles**, 19,838 vertices; UV channels 3; material slots 7; collision primitives 3; Nanite unchecked. Approx Size (יחידה לא מסומנת): `296 x 481 x 762`.

זכויות: `exact_listing_identified_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_Palm_01_01_G](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/41_Palm01_whole__1.jpg)

### 11. SM_Palm_01_06_G

ID: `current_Palms_Pack_01__Meshes__SM_Palm_01_06_G`

Unreal: `/Game/Palms_Pack_01/Meshes/SM_Palm_01_06_G.SM_Palm_01_06_G`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Palms_Pack_01\Meshes\SM_Palm_01_06_G.uasset`

[measured] דקל ירוק זקוף יותר, בעל כתר מדורג ומניפה עליונה. צללית שונה מ־Palm01.

[inference] keep בנפרד מ־Palm01; אין ראיה לכפילות.

[measured] LOD0: **20,729 triangles**, 21,422 vertices; UV channels 3; material slots 7; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `331 x 326 x 648`.

זכויות: `exact_listing_identified_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_Palm_01_06_G](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/46_Palm06_whole__2.jpg)

### 12. SM_Palm_01_12_G

ID: `current_Palms_Pack_01__Meshes__SM_Palm_01_12_G`

Unreal: `/Game/Palms_Pack_01/Meshes/SM_Palm_01_12_G.SM_Palm_01_12_G`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Palms_Pack_01\Meshes\SM_Palm_01_12_G.uasset`

[measured] גזע קצר מאוד וכתר מניפות ירוק דליל ורחב. צורת צמיחה נמוכה שונה מן הדקלים הבוגרים.

[inference] keep בנפרד; אינו רק עותק מוקטן של דקל בוגר.

[measured] LOD0: **2,915 triangles**, 3,006 vertices; UV channels 3; material slots 6; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `172 x 170 x 126`.

זכויות: `exact_listing_identified_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_Palm_01_12_G](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/48_Palm12_whole__1.jpg)

### 13. SM_Palm_01_13_Dry

ID: `current_Palms_Pack_01__Meshes__SM_Palm_01_13_Dry`

Unreal: `/Game/Palms_Pack_01/Meshes/SM_Palm_01_13_Dry.SM_Palm_01_13_Dry`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Palms_Pack_01\Meshes\SM_Palm_01_13_Dry.uasset`

[measured] דקל גבוה וצר עם עלים חומים־אפורים תלויים וללא כתר ירוק שנראה בתצוגה.

[inference] review כמצב יבש נקודתי; לא ברירת מחדל לשתילה לפני המלחמה.

[measured] LOD0: **23,221 triangles**, 23,856 vertices; UV channels 3; material slots 5; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `298 x 289 x 854`.

זכויות: `exact_listing_identified_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_Palm_01_13_Dry](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/50_Palm13_whole__1.jpg)

### 14. SM_Palm_01_15_Dry_Fallen

ID: `current_Palms_Pack_01__Meshes__SM_Palm_01_15_Dry_Fallen`

Unreal: `/Game/Palms_Pack_01/Meshes/SM_Palm_01_15_Dry_Fallen.SM_Palm_01_15_Dry_Fallen`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Palms_Pack_01\Meshes\SM_Palm_01_15_Dry_Fallen.uasset`

[measured] דקל יבש נפול בשלמותו, עם שורשים גלויים וכתר יבש.

[inference] review למצב נפול בלבד ובהתאם לראיית מקום/זמן; אין להציב כשתילה רגילה.

[measured] LOD0: **31,198 triangles**, 31,199 vertices; UV channels 3; material slots 5; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `738 x 247 x 289`.

זכויות: `exact_listing_identified_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_Palm_01_15_Dry_Fallen](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/52_Palm15_whole__1.jpg)

### 15. SM_H0015_Building_02

ID: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0015_Building_02`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0015_Building_02.SM_H0015_Building_02`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0015_Building_02.uasset`

[measured] בניין שלם עם חמש שורות חזית עליונות מעל מסחר/כניסות ומבני גג נסוגים; מרפסות פתוחות ובליטות מזוגגות, כביסה וצלחות.

[inference] keep כמועמד לבניין מגורים מעל מסחר. לשמר גובה, מרפסות וגג; אינו מודול BG.

[measured] LOD0: **201,057 triangles**, 211,808 vertices; UV channels 2; material slots 4; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `2,034 x 1,170 x 2,417`.

זכויות: `owner_confirmed_for_technical_qualification`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_H0015_Building_02](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/55_H0015_whole__1.jpg)

### 16. SM_H0905_Arab_x1_fbx

ID: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0905_Arab_x1_fbx`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0905_Arab_x1_fbx.SM_H0905_Arab_x1_fbx`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0905_Arab_x1_fbx.uasset`

[measured] מבנה ארוך ונמוך בעל כיפה, חמישה פתחים מחודדים סגורים ופרטים מעוטרים.

[inference] review כמבנה מיוחד; לא בסיס כללי למגורים נמוכים.

[measured] LOD0: **6,075 triangles**, 8,496 vertices; UV channels 2; material slots 1; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `2,192 x 1,021 x 963`.

זכויות: `owner_confirmed_for_technical_qualification`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_H0905_Arab_x1_fbx](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/59_H0905_whole__1.jpg)

### 17. SM_H0906_Arab_x2_fbx

ID: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0906_Arab_x2_fbx`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0906_Arab_x2_fbx.SM_H0906_Arab_x2_fbx`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0906_Arab_x2_fbx.uasset`

[measured] מבנה צר ומצולע בשתי קומות צורניות עם כיפה, סבכות ופתחים סגורים.

[inference] review כמגדל/ביתן מיוחד; שונה מן H0905 הארוך ומן H0907 הרחב.

[measured] LOD0: **4,361 triangles**, 6,398 vertices; UV channels 2; material slots 1; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `789 x 794 x 1,367`.

זכויות: `owner_confirmed_for_technical_qualification`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_H0906_Arab_x2_fbx](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/61_H0906_whole__1.jpg)

### 18. B18_Win_Wall_3x3_Set

ID: `current_ProceduralBuildingGenerator__Meshes__Wall__B18_Win_Wall_3x3_Set`

Unreal: `/Game/ProceduralBuildingGenerator/Meshes/Wall/B18_Win_Wall_3x3_Set.B18_Win_Wall_3x3_Set`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ProceduralBuildingGenerator\Meshes\Wall\B18_Win_Wall_3x3_Set.uasset`

[measured] מקטע לבנים עם חלון צר וגבוה בעל שני לוחות. בצד הנגדי נראה גמר אריחים בהיר עם חלון.

[inference] review: מקטע בעל פתח צר; גמר הלבנים והחיבורים ל־BG אינם מוכשרים.

[measured] LOD0: **280 triangles**, 446 vertices; UV channels 2; material slots 6; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `27 x 300 x 300`.

זכויות: `acquisition_record_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של B18_Win_Wall_3x3_Set](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/63_B18_whole__1.jpg)

### 19. B55_2Win_Wall_3x3_Set

ID: `current_ProceduralBuildingGenerator__Meshes__Wall__B55_2Win_Wall_3x3_Set`

Unreal: `/Game/ProceduralBuildingGenerator/Meshes/Wall/B55_2Win_Wall_3x3_Set.B55_2Win_Wall_3x3_Set`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ProceduralBuildingGenerator\Meshes\Wall\B55_2Win_Wall_3x3_Set.uasset`

[measured] פתח רחב יחיד המחולק לשתי עמודות זיגוג וארבעה לוחות, עם משקוף ואדן.

[inference] review: לשמר את קצב הפתח הרחב; אין מדובר בשני פתחים עצמאיים בקיר.

[measured] LOD0: **282 triangles**, 392 vertices; UV channels 2; material slots 5; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `34 x 300 x 300`.

זכויות: `acquisition_record_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של B55_2Win_Wall_3x3_Set](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/67_B55_Front__1.jpg)

### 20. B93_Win_Extruded_Wall_3x3_Var2_Set

ID: `current_ProceduralBuildingGenerator__Meshes__Wall__B93_Win_Extruded_Wall_3x3_Var2_Set`

Unreal: `/Game/ProceduralBuildingGenerator/Meshes/Wall/B93_Win_Extruded_Wall_3x3_Var2_Set.B93_Win_Extruded_Wall_3x3_Var2_Set`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ProceduralBuildingGenerator\Meshes\Wall\B93_Win_Extruded_Wall_3x3_Var2_Set.uasset`

[measured] מקטע לבנים בעל תבליט עמוק סביב חלון מרובה לוחות, משקוף ואדן.

[inference] review: לשמר עומק ושונות בחלוקה לעומת B18/B55.

[measured] LOD0: **932 triangles**, 1,275 vertices; UV channels 2; material slots 4; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `50 x 300 x 300`.

זכויות: `acquisition_record_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של B93_Win_Extruded_Wall_3x3_Var2_Set](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/69_B93_whole__1.jpg)

### 21. SM_wall_windows_4x4_open

ID: `current_ModularCourtyard__Meshes__SM_wall_windows_4x4_open`

Unreal: `/Game/ModularCourtyard/Meshes/SM_wall_windows_4x4_open.SM_wall_windows_4x4_open`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ModularCourtyard\Meshes\SM_wall_windows_4x4_open.uasset`

[measured] דומה למקטע החלון הסגור, עם אזור שחור פתוח קטן בחלון השמאלי וחומר M_Dark_Empty נוסף. גב הקיר עדיין אטום.

[inference] review כווריאנט מצב חלון; הסיומת open אינה הוכחה למעבר דרך הקיר.

[measured] LOD0: **660 triangles**, 924 vertices; UV channels 2; material slots 5; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `54 x 400 x 400`.

זכויות: `acquisition_record_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של SM_wall_windows_4x4_open](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/72_Courtyard_open_whole__1.jpg)

### 22. store_front_windows_intact_4x1_a

ID: `current_ModularBuildingSet__Meshes__Store_fronts__store_front_windows_intact_4x1_a`

Unreal: `/Game/ModularBuildingSet/Meshes/Store_fronts/store_front_windows_intact_4x1_a.store_front_windows_intact_4x1_a`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ModularBuildingSet\Meshes\Store_fronts\store_front_windows_intact_4x1_a.uasset`

[measured] חזית חנות כהה עם ארבעה bays, שמונה לוחות זכוכית ופס אריחים תחתון. רוב המסגרות והבסיס אינם נראים במבט Back.

[inference] review כחזית חיצונית עם backing; לא קיר פנים מוגמר.

[measured] LOD0: **488 triangles**, 946 vertices; UV channels 2; material slots 4; collision primitives 1; Nanite unchecked. Approx Size (יחידה לא מסומנת): `35 x 600 x 394`.

זכויות: `acquisition_record_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של store_front_windows_intact_4x1_a](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/75_Storefront_exterior_whole__1.jpg)

### 23. store_front_windows_intact_4x1_a

ID: `current_ModularBuildingSet__Meshes__Store_fronts_interiors__store_front_windows_intact_4x1_a`

Unreal: `/Game/ModularBuildingSet/Meshes/Store_fronts_interiors/store_front_windows_intact_4x1_a.store_front_windows_intact_4x1_a`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ModularBuildingSet\Meshes\Store_fronts_interiors\store_front_windows_intact_4x1_a.uasset`

[measured] אותו קצב חזית, אבל הזיגוג מאפשר ראייה דרכו, יש עומק וחלקי חזרה נוספים והמסגרות/בסיס נראים גם במבט Back. נראה חריץ אנכי בהיר ליד התמיכה השמאלית הפנימית.

[inference] review בנפרד כגרסה הנראית גם מבפנים; לבדוק את החריץ והתפרים. אין לאחד עם הגרסה החיצונית.

[measured] LOD0: **798 triangles**, 1,528 vertices; UV channels 3; material slots 3; collision primitives 2; Nanite unchecked. Approx Size (יחידה לא מסומנת): `117 x 600 x 394`.

זכויות: `acquisition_record_terms_unverified`; ללא שינוי בהיקף האישור. [not run] התאמת תפקיד סופית, placement ו־Houdini.

![תצוגה מקורית של store_front_windows_intact_4x1_a](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/79_Storefront_interior_reverse__1.jpg)

## צמצום ורצף בדיקה

שלושת הדקלים הירוקים שנצפו שומרים הבדלי צללית וצמיחה; היבש והנפול הם מצבים נפרדים. אין להסיק שה־11 שטרם נבדקו מיותרים. גם B18/B55/B93, H0905/H0906/H0907 ושתי גרסאות חלון החנות אינם כפילויות מוכחות. תת־הקבוצה ההצעתית גדלה ל־133 רשומות / 174 נתיבי חברים בגלל גרסת החנות הפנימית. זה עדיין אינו מינימום חזותי מוכח.

המשך הבדיקה המדויק נמצא ב־`../NEXT_TASKS.md`. אבחון Acacia ותפרי החנות קודמים להכשרה; כל שינוי חומר/יבוא/יצירה דורש GO נפרד בהתאם לגבולות המשימה. בדיקות צפייה נוספות כבר מורשות, בכפוף לנעילה חדשה. CONTRACT v0.6 נשאר DRAFT.
