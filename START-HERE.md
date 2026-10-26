# ابدأ من هنا — دليل الحساب الجديد (آخر تحديث: 26 ت10 2026)

> هذا الملف مكتوب لمن يفتح المشروع لأول مرة ويكمل من حيث توقفنا.
> اقرأه كاملاً (5 دقائق)، ثم نفّذ «التحقق السريع»، ثم ابدأ من «أين تكمل».
> المرجع التفصيلي الكامل: **[HANDOFF.md](HANDOFF.md)** — اقرأه بعد هذا الملف.

---

## 0) الحالة في سطرين

مشروع تخرّج/تطبيق رسمي لكلية علوم الحاسوب — جامعة القادسية: تطبيق Flutter + خلفية FastAPI/PostgreSQL + لوحة تحكم React.
**المنجز والمتحقَّق:** المصادقة وربط الجهاز، استيراد الطلاب، الحضور (QR متجدد + موقع + قائمة لحظية)، الجدول، **الدرجات/المواد/الإعلانات/الإشعارات (API)**، و**شاشات الحضور والجدول والمواد والدرجات في التطبيق**، وأول **APK**.
**التالي:** N7 — الاعتماد التجريبي (شعبة واحدة لأسبوعين و20 مختبِراً في Play المغلقة).
لوحة التحكم اكتملت (سبع شاشات). متبقٍّ من النشر: صور Docker (Docker غير مثبت) وTLS (يحتاج سيرفر الجامعة).

الأرقام الحقيقية الآن: **API 93/93 على SQLite و93/93 على PostgreSQL** (ترحيلات 0001–0004) ·
**Flutter 65/65** و`analyze` نظيف و**APK 67.8MB** · **لوحة التحكم**: سبع شاشات، بناء ناجح، والأربع الجديدة مُجرَّبة يدوياً ·
**نسخ/استرجاع مُجرَّب** (5/0/1 · 0003) · `/health` عميق (revision 0004) · `alembic` نظيف · **CI أخضر 3/3**.
غير متحقق: صور Docker، Redis فعلي، TLS، وعرض الشاشات على سطح مكتب عريض.

---

## 1) كيف تفتح المشروع

**الأفضل — استنسخ من GitHub** (المستودع عام):
```powershell
git clone https://github.com/JJ36t/csit-app.git
cd csit-app
```
**أو إن كنت على نفس جهاز صاحب المشروع**، فالمسار الجاهز:
```
C:\Users\hmt1\AppData\Roaming\AutoClaw-oversea-official\accounts\90bf5e4257a511df50abcd3c96ca6610cc4a4ed815f7645029a1b06a0779b811\projects\Default\csit-app
```

## 2) ماذا يحتاج الجهاز

| الأداة | المسار/الملاحظة |
|---|---|
| Flutter 3.47.8 (Dart 3.13.7) | `C:\Users\hmt1\develop\flutter\bin` (ليس على PATH افتراضياً) |
| Python 3.13 | `python -m pip install -r api/requirements-dev.txt` |
| PostgreSQL 18.6 | خدمة `postgresql-x64-18` · قواعد `csit` (تطوير) و`csit_test` (اختبار) · أدواته في `C:\Program Files\PostgreSQL\18\bin` |
| git | `C:\Program Files\Git\cmd` (ليس على PATH افتراضياً) |
| Android (لبناء APK) | Android Studio + JBR في `C:\Program Files\Android\Android Studio\jbr` |

> **كلمة مرور postgres** يزوّدك بها صاحب المشروع شفهياً/في المحادثة. **لا تُكتب في أي ملف ولا في git** — تُمرَّر كمتغيّر بيئة.

**بيئة PowerShell قبل أي أمر** (جلسات هذه البيئة ناقصة متغيّرات):
```powershell
$env:SystemRoot='C:\Windows'; $env:ProgramFiles='C:\Program Files'; ${env:ProgramFiles(x86)}='C:\Program Files (x86)'
$env:ComSpec='C:\Windows\System32\cmd.exe'; $env:TEMP='C:\Windows\Temp'; $env:TMP='C:\Windows\Temp'
$env:LOCALAPPDATA="$env:USERPROFILE\AppData\Local"; $env:APPDATA="$env:USERPROFILE\AppData\Roaming"
$env:PUB_CACHE="$env:LOCALAPPDATA\Pub\Cache"
$env:Path="C:\Users\hmt1\develop\flutter\bin;C:\Program Files\Git\cmd;C:\Windows\System32;C:\Windows;"+$env:Path
```

---

## 3) التحقق السريع (نفّذه فعلاً قبل أي تعديل — 6 دقائق)

```powershell
# API على SQLite — يجب 93/93
cd api; $env:DATABASE_URL='sqlite:///./test_api.db'; python -m pytest tests -q

# API على PostgreSQL — يجب 93/93 (يحتاج كلمة مرور postgres من صاحب المشروع)
$env:PGPASSWORD='<من صاحب المشروع>'
$env:DATABASE_URL='postgresql+psycopg://postgres@127.0.0.1:5432/csit_test'; python -m pytest tests -q

# الترحيلات — يجب: No new upgrade operations detected
$env:DATABASE_URL='postgresql+psycopg://postgres@127.0.0.1:5432/csit'; python -m alembic upgrade head; python -m alembic check

# التطبيق — يجب 0 ملاحظات و65/65
cd ../app; flutter pub get; flutter gen-l10n; flutter analyze; flutter test

# لوحة التحكم — يجب بناء ناجح
cd ../admin; npm run build

# فحص عميق ونسخ احتياطي (يحتاج PostgreSQL + كلمة المرور)
cd ../api; python scripts/backup_db.py; python scripts/verify_restore.py
```

إن اختلف رقم واحد عن الأعلى فاعلم أن هناك تغييراً غير متوقّع — توقّف واقرأ `git log`.

---

## 4) تشغيل الخدمات محلياً (عرض حي)

```powershell
cd api
python -m alembic upgrade head          # على قاعدة csit
python scripts/seed.py                  # الأقسام الأربعة + السنة
python scripts/demo_seed.py             # تدريسي/طالبان/مادة/حصة اليوم
python scripts/create_admin.py ADMIN-001 "مدير الكلية" "Admin#2026"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# نافذة ثانية: لوحة التحكم على 5173 (proxy /api إلى 8000)
cd admin; npm run dev

# نافذة ثالثة: تطبيق الويب على 8080
subst X: <مسار csit-app المطلق>      # لتفادي حد ويندوز 260 حرفاً
cd X:\app; flutter build web --release --dart-define=API_BASE_URL=http://127.0.0.1:8000
cd build\web; python -m http.server 8080 --bind 127.0.0.1
```

**حسابات التجربة:** طالب `S-100` · تدريسي `T-100` (كلمة المرور `Test#12345`) · مدير `ADMIN-001` (`Admin#2026`).
**رسالة «هذا الحساب مرتبط بجهاز آخر»** = قاعدة الجهاز الواحد؛ الحل للتطوير: `python scripts/dev_reset_devices.py [رقم]`.

---

## 5) خريطة سريعة للكود

```
api/app/
  routers/   auth, admin_users, admin_students, admin_timetable, attendance, timetable,
             departments, health, grades, materials, announcements, notifications, offerings
  services/  attendance(QR/مسافة), access(النطاقات), audit, import_students, rate_limit,
             sessions, storage(ملفات), file_links(روابط موقّعة), notifications(جمهور)
  models/    identity, academic, timetable, attendance, content, comms (+ enums.py)
app/lib/
  core/      network(api_client, authed_dio), storage(token_store), platform(link_opener),
             app_services.dart, utils/date_utils.dart
  features/  auth, home, attendance{scan, live, sessions}, timetable{data, presentation},
             materials, grades, announcements, notifications, profile_settings
  l10n/app_ar.arb   ← كل النصوص العربية هنا حصراً
admin/src/   App.tsx, api.ts, pages/{LoginPage, StudentsPage, TimetablePage, GradesPage,
                                    AnnouncementsPage, UsersPage, AuditPage, DashboardPage}
```

**قواعد ملزمة:** نصوص الواجهة من `app_ar.arb` فقط · تعليقات/توثيق بالعربية · كل عملية حساسة (حضور/درجة/جهاز/كلمة مرور/استيراد) عبر `audit_logs` · القوائم تُخزَّن بقيمها الصغيرة عبر `models.enums.SAEnum` · الوقت UTC والعرض بتوقيت بغداد.

---

## 6) أين تكمل بالضبط — **N7: الاعتماد التجريبي**

الهدف: تشغيل حقيقي محدود يجمع ملاحظات قبل التوسع (المرحلة 6 من الخطة).

1. **شعبة واحدة لأسبوعين:** تدريسي واحد + مادة واحدة + 10–20 طالباً حقيقياً (بعد الموافقة الكتابية على البيانات).
2. **الدرجات:** تقييم واحد يُدخل ويُنشر فعلياً، ومطابقة ما يراه الطالب في التطبيق بما في اللوحة.
3. **الحضور:** فتح جلسة من التطبيق ومسح من هاتف حقيقي — **الكاميرا لم تُجرَّب بعد، وهي أهم بند متبقٍ**.
4. **Play المغلقة:** 20 مختبِراً لمدة 14 يوماً، ثم تقرير أخطاء مصنّف (حرج/مهم/تحسين) وإصلاح الحرج.

**معايير القبول:** تقرير اعتماد موثّق (ما جُرّب، من جرّبه، النتيجة) · صفر أخطاء حرجة مفتوحة ·
تحديث `HANDOFF.md` بما تحقق فعلاً على أجهزة حقيقية.

**بالتوازي (اختياري):** بناء صور Docker على جهاز فيه Docker، ثم TLS أمام Nginx على سيرفر الجامعة.

## 7) الفخاخ التي كلّفتنا وقتاً (لا تكرّرها)

1. **حد ويندوز 260 حرفاً**: مسار المساحة ~160 حرفاً؛ بناء APK من المسار الأصلي يفشل بخط `CupertinoIcons`. الحل: `subst X: <المسار>` والبناء من `X:\app` (مع `kotlin.incremental=false` و`kotlin.compiler.execution.strategy=in-process` في `app/android/gradle.properties`).
2. **`AppLocalizations.of(context)` داخل `initState`** يرمي assertion ويترك المؤشر دوّاراً للأبد — اقرأها بعد `await` مع فحص `mounted`.
3. **ListView في الاختبارات يبني أبناءه بكسل** — اضبط `tester.view.physicalSize` (هاتف عمودي) وإلا فشلت `findsOneWidget` زوراً.
4. **ARB بمعاملات** يحتاج `@key.placeholders` وإلا يفشل `gen-l10n`؛ الأعداد `int`.
5. **UUID في الاختبارات**: مرّر `uuid.UUID` لا نصاً عند `db.get`.
6. **SQLite يعيد تواريخ بلا منطقة زمنية** → استخدم `app.security.as_utc()` قبل المقارنة.
7. **git ليس على PATH**: `C:\Program Files\Git\cmd\git.exe`.
8. **`flutter build web` يحذّر من خطوط Cupertino** إن غاب `cupertino_icons` (موجود الآن).
9. **سكربتات `smoke_*` تربط جهازاً للحساب** (قاعدة الجهاز الواحد): بعد تشغيلها يفشل دخول المدير من
   المتصفح بـ«مرتبط بجهاز آخر». الحل: `python scripts/dev_reset_devices.py` ثم الدخول من جديد.
10. **Docker غير مثبت** على جهاز التطوير: `docker compose` و`nginx -t` غير قابلين للتشغيل — حزمة النشر
    مفحوصة ملفياً فقط. و**pg_dump/pg_restore ليسا على PATH**: السكربتات تكتشفان `C:\Program Files\PostgreSQL\18\bin`.
11. **Redis غير مثبت** محلياً: مسار Redis مغطّى بـ`fakeredis` في الاختبارات، وليس بخدمة حقيقية.
12. **`audit_logs` بلا طابع زمني قبل ترحيل `0004`:** أي قاعدة قديمة تحتاج `alembic upgrade head` قبل شاشة سجل التدقيق، وإلا فشل الاستعلام على العمود الجديد.
13. **اختبار يعتمد على `DateTime.now()` قد يعبر منتصف الليل** (فشل اختبار الجدول بعد 22:00 بغداد):
    ثبّت اللحظات على صباح اليوم بتوقيت بغداد (`todayUtc.add(hours: 5)`) بدل `now.add(hours: 2)`.

---

## 8) لا تفعل

- لا **force-push** ولا حذف تاريخ المستودع (CI أخضر عليه).
- لا كلمات مرور/مفاتيح في الملفات؛ `JWT_SECRET` من البيئة.
- لا تحذف اختباراً ولا تُضعف تأكيداً لتمرير بناء.
- لا تعدّل `api/migrations/versions/0001` أو `0002` (تاريخ منشور) — أضف ترحيلاً جديداً.
- **لا تسليم بلا تشغيل**: شغّل الاختبارات على القاعدتين + `alembic check` + `flutter analyze/test` قبل أي ادعاء نجاح، واذكر ما لم تتحقق منه.

---

## 9) أين التفاصيل

| الملف | المحتوى |
|---|---|
| [HANDOFF.md](HANDOFF.md) | الحالة الكاملة، أوامر التحقق، الفخاخ (19)، معايير قبول كل مرحلة |
| [api/README.md](api/README.md) | النقاط، السكربتات، قرارات التصميم، الفحوص |
| [app/README.md](app/README.md) | الشاشات، الاعتماديات، الاختبارات، بناء APK |
| [admin/README.md](admin/README.md) | لوحة التحكم |
| [design/screens.html](design/screens.html) | نموذج الشاشات الثماني (افتحه في المتصفح) |
| [README.md](README.md) | الملخص التنفيذي والقرارات السبعة |
