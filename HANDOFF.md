# حالة المشروع وخطة المتابعة — تطبيق كلية علوم الحاسوب وتكنولوجيا المعلومات

> **لمن يقرأ هذا الملف:** أنت تكمل عملاً جارياً. اقرأ الملف كاملاً قبل أول تعديل، ثم نفّذ «الخطوات التالية» بالترتيب.
> لا تعِد بناء ما هو مكتمل، ولا تعلن نجاح شيء لم تشغّله فعلاً.
> آخر تحديث: **الاثنين 26 تشرين الأول 2026**.

---

## 0) ابدأ من هنا — خلاصة في عشرة أسطر

1. المشروع: تطبيق أندرويد لكلية علوم الحاسوب وتكنولوجيا المعلومات — جامعة القادسية، بخلفية FastAPI/PostgreSQL ولوحة تحكم ويب.
2. المستودع: `csit-app/` وفيه `api/` و`app/` (Flutter) و`admin/` (React) و`design/` (نموذج الشاشات).
3. **مكتمل ومتحقَّق منه:** المصادقة وربط الجهاز، استيراد الطلاب من Excel، الحضور (QR متجدد + موقع + لحظي + تقارير)، الجدول (حصص + تعارضات + تغييرات مؤرخة)، فهرس «جهاز نشط واحد»، ودرجات ومواد وإعلانات وإشعارات (N3)، وملف CI.
4. الحالة الحالية للاختبارات: **69/69 على SQLite** (الترحيلات 0001–0003)، و`alembic check` نظيف، و`smoke_n4` أخضر عبر HTTP؛ وFlutter **43/43**. آخر تشغيل على PostgreSQL كان **65/65** قبل N4 (كلمة مرور `postgres` لم تكن متوفرة في جلسة N4).
5. تطبيق Flutter: المصادقة + **N1 الحضور** + **N2 الجدول والمواد والدرجات** + **APK ناجح** (67.5MB)؛ تبقى الإعلانات والملف الشخصي. ولوحة التحكم: **N4 منجز** — الطلاب/الجدول/الدرجات.
6. **التالي فوراً:** N5 (Redis + نسخ احتياطي + `docker-compose`/Nginx)، ثم بقية شاشات اللوحة (الإعلانات/المستخدمون/سجل التدقيق).
7. **git مهيأ ومدفوع إلى GitHub**: المستودع `https://github.com/JJ36t/csit-app` — و**CI يعمل فعلياً ونجح بالكامل (3/3 وظائف)** في أول تشغيل.
8. **Android SDK مثبّت** وبناء APK يعمل عبر قرص قصير `subst X:` (انظر 5.6)؛ تجربة الكاميرا على هاتف حقيقي لم تُجرّب بعد.
9. المستخدم (صاحب المشروع) ينتظر إنجاز بنود إدارية موثّقة في القسم 8 (قواعد الغياب، الجدول الرسمي، عيّنة بيانات…).
10. القاعدة الذهبية: **لا تسليم بدون تشغيل**، واذكر دائماً ما تحققت منه وما لم تتحقق منه.

---

## 1) المشروع وقراراته المحسومة

**الهدف:** تطبيق رسمي يجمع «يوم الطالب»: الجدول، الحضور بمسح QR، المواد، الإعلانات، الأخبار، والدرجات — مع لوحة تحكم ويب للإدارة.

**المرجعان الأصليان:**
- خطة التنفيذ: `.zwork/attachments/71ed3846-bc74-4c9f-87ae-f000c9f115c2/خطة تطبيق كلية علوم الحاسوب وتكنولوجيا المعلومات – جامعة القادسية.pdf` (21 صفحة، 16 قسماً، مؤرخة 22 تشرين الأول 2026).
- سجل القرارات: `سجل القرارات وتحديثات الخطة.docx` في جذر مساحة العمل (7 قرارات + أثرها + المراحل التسع).

**القرارات السبعة (لا تُنقض):**

| # | القرار |
|---|---|
| 1 | توجد رعاية رسمية من الكلية — يتبقى: موافقة كتابية على استخدام بيانات الطلاب + تسمية مسؤول بيانات |
| 2 | الاستضافة على **سيرفر جامعي** (PostgreSQL + Docker)، لا VPS مدفوع |
| 3 | **الدرجات وأعمال السنة ضمن الإطلاق الأول** (لا تُؤجَّل إلى V2) |
| 4 | قواعد الغياب/التأخير تُحدَّد لاحقاً؛ الافتراضي الآن: التدريسي يسجّل حاضر/غائب، والقواعد إعدادات قابلة للتهيئة |
| 5 | **أربعة أقسام**: علوم الحاسوب، نظم المعلومات، الأنظمة الطبية، الأمن السيبراني — والدراسة **صباحي ومسائي** |
| 6 | **مطوّر فرد** → Modular Monolith، أولوية للميزات عالية الأثر |
| 7 | الاسم «علوم الحاسوب»، المعرّف `iq.edu.qu.csit` (لا يتغيّر بعد النشر) |

---

## 2) أين وصلنا — سجل ما أُنجز

**المرحلة 1 — الأساس (25 ت10 2026):**
- مستودع موحّد `csit-app/{app,api,admin}` + `.gitignore` + READMEs.
- الترحيل `0001`: **29 جدولاً** في ست مجموعات كما في القسم 8 من الخطة، UUID + طوابع UTC + حذف ناعم + القيود الفريدة (`uq_attendance_once`، `uq_grade_once`، `uq_enrollment_once`، `uq_announcement_read_once`، `uq_group_identity`، `uq_offering_identity`) + فهرس `(offering_id, weekday)`.
- القوائم (Enums) تُخزَّن بقيم نصية صغيرة (`student`, `present`, `morning`) عبر `values_callable` في `app/models/enums.py`.
- `scripts/seed.py`: الأقسام الأربعة + السنة 2026–2027.
- لوحة تحكم React/Vite/AntD أولية (تنقّل بسبعة أقسام، RTL) وبناؤها ناجح.

**المرحلة 2 — أساس التطبيق (25 ت10 2026):**
- مصادقة: `POST /auth/login` (JWT وصول 15 دقيقة + تجديد 30 يوماً بالتناوب، وكشف إعادة استخدام رمز ملغى يُنهي كل الجلسات)، `/refresh`، `/logout`، `/change-password` (يُلغي الجلسات)، `/me`.
- ربط الجهاز: جهاز نشط واحد لكل حساب، بصمة ثابتة، رفض الجهاز الثاني (403 `device_change_requires_approval`).
- إدارة: `POST /admin/users/{id}/device/reset` و`/reset-password` بنطاق (مدير الكلية / رئيس القسم لقسمه).
- استيراد الطلاب: `POST /admin/students/import` (فحص `dry_run=true` افتراضياً، تقرير أخطاء عربي برقم الصف والعمود والسبب، معاملة واحدة، إنشاء الشعب تلقائياً)، `GET /admin/students/template`، `GET /admin/students`.
- سجل تدقيق `audit_logs` لكل: دخول ناجح/فاشل، رفض تغيير جهاز، إعادة ضبط جهاز، إعادة ضبط كلمة مرور، تغيير كلمة مرور، استيراد طلاب.
- حدّ محاولات: فشل الدخول فقط (5/دقيقة)، ويُصفَّر بالنجاح.
- Flutter: تخزين آمن للرموز، Dio بتجديد تلقائي عند 401، شاشة دخول عربية، شاشة تغيير كلمة مرور، موجّه محمي، كل النصوص في `app_ar.arb`.

**المرحلة 3 — الحضور والجدول (26 ت10 2026):**
- جلسات: `POST /sessions/{id}/open` (رمز QR = `<window>.<HMAC-SHA256(secret, session:window)>` يتجدد كل 20 ثانية، سماحية نافذة واحدة)، `/close` (يسجّل غياب من لم يُسجّل)، `GET /sessions/{id}/live` (عداد + قائمة + الرمز الحالي).
- مسح: `POST /attendance/scan` بترتيب: جلسة مفتوحة ← رمز ساري (410 منتهٍ / 400 تالف) ← طالب مسجَّل ← جهاز مربوط نشط ← لا تسجيل مسبق (409)؛ حاضر/متأخر حسب `attendance_grace_minutes`، والموقع خارج نطاق القاعة/الحرم → `flagged=true` و`flag_reason=outside_campus:<m>` **دون رفض**.
- تعديل يدوي: `PATCH /attendance/{id}` مدقَّق (قبل/بعد).
- تقارير: `GET /attendance/summary` (الطالب)، `GET /offerings/{id}/attendance`، `GET /offerings/{id}/attendance/report`.
- جدول: `GET /timetable?from=&to=`، `GET /timetable/changes`؛ إدارة: `POST /admin/timetable/rooms`، `/slots` (كشف تعارض قاعة/تدريسي/شعبة + توليد جلسات الفصل تلقائياً)، `/changes` (إلغاء/نقل/إضافة مؤرخة).
- الترحيل `0002`: فهرس فريد جزئي `uq_devices_one_active_per_user` على `devices(user_id) WHERE status='active'` (PostgreSQL وSQLite)، ومثبَّت أيضاً في النموذج لتفادي انحراف `alembic check`.
- `.github/workflows/ci.yml`: ثلاث وظائف (API على PostgreSQL 16 + Flutter + لوحة التحكم).
- `design/screens.html`: نموذج ثماني شاشات، كل إطار 390×844، عربي RTL، بلا أي مرجع خارجي (متحقَّق برمجياً).

**المرحلة 4 — N1: الحضور في Flutter (26 ت10 2026):**
- اعتماديات: `mobile_scanner` (قراءة QR)، `qr_flutter` (عرض رمز الجلسة)، `geolocator` (الموقع، اختياري)، `cupertino_icons`؛ وصلاحيات أندرويد في الـManifest: CAMERA + ACCESS_FINE/COARSE_LOCATION.
- صيغة رمز QR المعروض: `csit:v1:<session_id>:<token>` — يبنيها تطبيق التدريسي من `GET /sessions/{id}/live` (لا تعديل على الـAPI)، ويفكّها تطبيق الطالب في `features/attendance/data/qr_payload.dart`.
- شاشة المسح (طالب): كاميرا الهاتف عبر غلاف `attendance_scanner.dart` (قابل للحقن)، ترسل `POST /attendance/scan` بـ`device_id` المحفوظ عند الدخول والموقع من `geolocator` (تعذّره = مسح بلا موقع، والخادم يعلّمه «مشكوكاً»)، وبطاقة نتيجة آخر مسح (حاضر/متأخر/مشكوك + سبب `outside_campus:<m>m` أو `no_location`) ورسالة الخادم.
- شاشة حصص اليوم (تدريسي): `GET /timetable` وتصفية حصص اليوم بتوقيت بغداد، ثم الانتقال للقائمة اللحظية.
- القائمة اللحظية: `GET /sessions/{id}/live` بتحديث دوري (10 ثوانٍ، يُلغى عند مغادرة الشاشة)، عدّاد حضور + نسبة + قائمة بشرائح تصفية (الكل/حاضر/متأخر/مشكوك/غائب)، فتح الجلسة `/open` وإغلاقها `/close` بتأكيد (يعرض «سُجّل غياب N»)، وQR متجدد من `qr_flutter`.
- بنية مشتركة: استُخرج منطق التجديد عند 401 إلى `core/network/authed_dio.dart` (يستخدمه HttpAuthApi وHttpAttendanceApi)، ويُحفظ `device_id` في التخزين الآمن عند كل دخول، و`SessionController.expire()` تُفرغ الجلسة عند 401 فتُعيد الموجّه لشاشة الدخول.
- اختبارات: 27/27 ببدائل في الذاكرة (++22 اختباراً جديداً: 3 لصيغة QR، 8 للمسح، 5 للقائمة اللحظية، 4 لحصص اليوم، 2 للتخزين الآمن).

**المرحلة 5 — N3: الدرجات والمواد والإعلانات والإشعارات (26 ت10 2026):**
- **الدرجات:** `POST /assessments` (وزن + درجة عظمى، حدّ مجموع الأوزان 100)، `POST /assessments/{id}/grades` (إدخال دفعي كمسودة، تحقق التسجيل والحد الأقصى، تدقيق قبل/بعد لكل درجة)، `POST /assessments/{id}/publish` (مدير الكلية فقط + إشعار الطلاب المسجَّلين + تدقيق)، `GET /offerings/{id}/grades` (مصفوفة + مجموع موزون)، `GET /offerings/{id}/grades/export` (Excel)، `GET /grades` (الطالب: المنشور فقط)، `DELETE /assessments/{id}` (غير منشور).
- **المواد:** رفع ملف PDF أو رابط (`POST /offerings/{id}/materials`) بتحقق النوع/الحجم (25MB افتراضياً) وتخزين بمفتاح عشوائي في `uploads/`، قراءة للطالب المسجَّل (المنشور فقط)، وتنزيل برابط موقّع HMAC عمره 10 دقائق (`GET /files/{id}/download?expires=&sig=`).
- **الإعلانات:** `POST /admin/announcements` بنطاق (كلية/قسم/مرحلة/شعبة/مادة) وصلاحيات نطاق + جدولة `publish_at`، خلاصة موجّهة `GET /announcements` بعلامة مقروء، و`POST /announcements/{id}/read`.
- **الإشعارات:** صندوق وارد `GET /notifications` + `read-all` + قراءة واحدة + `PUT /devices/fcm-token`؛ إنشاء جماعي عند نشر إعلان أو درجة.
- **الترحيل `0003`:** `files.original_name`، `announcements.stage`، وطوابع `notifications.created_at/updated_at`؛
- **CORS** لنطاقات localhost للتطوير، و`alembic check` نظيف بعد الترحيل.
- اختبارات: 19 جديدة (7 درجات، 5 مواد، 4 إعلانات، 3 إشعارات) — **62/62** على القاعدتين + `scripts/smoke_n3.py` عبر HTTP.

**المرحلة 6 — N2: الجدول والمواد والدرجات في Flutter (26 ت10 2026):**
- **الجدول:** شاشة بأيام (شرائح) تُقرأ من `GET /timetable` + `GET /timetable/changes`، مع لافتة تغييرات مؤرخة (إلغاء/نقل/إضافة) لكل يوم، و**تخزين محلي** (shared_preferences) يُعرض عند تعذر الشبكة مع لافتة «بيانات محفوظة من HH:mm».
- **المواد:** `GET /offerings` (نقطة جديدة: مواد المستخدم حسب دوره) ثم `GET /offerings/{id}/materials`، وفتح PDF برابط موقّع أو رابط فيديو عبر `url_launcher`.
- **الدرجات:** `GET /grades` — التقييمات المنشورة والدرجة والمجموع الموزون لكل مادة.
- **بنية مشتركة:** `AppServices` تحقن الواجهات الخمس في الموجّه/الرئيسية؛ `offering_id` أُضيف لعنصر الجدول؛ منطق نطاق العروض نُقل إلى `access.user_offering_ids` (شترك بين `/timetable` و`/offerings`).
- اختبارات: 16 جديدة في Flutter (5 جدول، 5 مواد، 4 درجات، 2 تخزين) → **43/43**، و3 جديدة في الـAPI → **65/65** على القاعدتين.

**المرحلة 7 — N4: شاشات لوحة التحكم (26 ت10 2026):**
- **الطلاب:** الأقسام تُقرأ من `GET /departments` بدل قائمة ثابتة، مع ترشيح القسم/المرحلة/الدراسة والبحث، والاستيراد بخطوتَي «فحص فقط» ثم «تنفيذ» وتقرير أخطاء عربي (صف/عمود/سبب).
- **الجدول:** الحصص في نطاق زمني (افتراضي اليوم ← +13 يوماً)، والتغييرات المؤرخة، والخطة الأسبوعية، وإدارة القاعات والحصص الأسبوعية والتغييرات المؤرخة — ورسالة التعارض تُعرض كنص `message_ar` مع رمز الخطأ كما يعيدها الخادم.
- **الدرجات:** اختيار المادة، التقييمات وأوزانها (مجموع 100 كإحصاء ظاهر)، مصفوفة (طلاب × تقييمات) بإدخال دفعي بتمييز الخلايا المعدّلة، حفظ كمسودات (طلب واحد لكل تقييم متغيّر)، نشر بتأكيد مقصور على مدير الكلية، إقفال الخلايا المنشورة، وتصدير Excel.
- **إضافات API مرافقة:** `GET /admin/timetable/rooms` · `GET /admin/timetable/slots` (بنطاق القسم لرئيس القسم)، و`slot_id` في عناصر `GET /timetable` — مع 4 اختبارات (القاعات، الحصص مع ترشيح المادة، ظهور `slot_id`، ومنع غير المدير) → **69/69**.
- **`scripts/smoke_n4.py`:** فحص HTTP للدورة كاملة (قائمة الطلاب/القالب ← تعارض قاعة 409 ← حصة أسبوعية ← إلغاء مؤرّخ ← درجة ← رفض نشر من التدريسي 403 ← نشر ← منع التعديل 409 ← تصدير Excel) — أخضر على خدمة حيّة.
- **تجربة يدوية:** `ADMIN-001` على `vite dev` نحو `uvicorn` (قاعدة SQLite للعرض): إنشاء قاعة، إنشاء تقييم، إدخال درجتين، حفظ (المجموع الموزون 8.5 و7)، نشر (إشعار 2)، إقفال الخلايا (‏`disabled`)، وظهور الحصة/الإلغاء في شاشة الجدول بعد التحديث.

---

## 3) حالة التحقق الحالية (أرقام حقيقية — أعدها قبل أي تسليم)

| الفحص | الأمر | النتيجة عند كتابة الملف |
|---|---|---|
| اختبارات API على SQLite | `pytest tests -q` | **69/69** |
| اختبارات API على PostgreSQL 18.6 | `DATABASE_URL=postgresql+psycopg://…` | **65/65** — آخر تشغيل قبل N4؛ لم يُعَد في جلسة N4 (كلمة المرور غير متوفرة)، والإضافات قراءة فقط |
| الترحيلات على PostgreSQL | `alembic upgrade head` + `alembic check` | 0001+0002+0003 · «No new upgrade operations detected» |
| دورة الإرجاع | `alembic downgrade base` ثم `upgrade head` | نظيفة |
| فحص HTTP شامل | `python scripts/smoke_e2e.py` | أخضر (مدير ← استيراد ← طالب ← منع جهاز ← إعادة ضبط ← رفض صلاحيات) |
| فحص N3 عبر HTTP | `python scripts/smoke_n3.py` | أخضر (تقييم ← درجة ← نشر ← درجة الطالب ← إعلان/إشعار ← مادة برابط موقّع) |
| فحص N4 عبر HTTP | `python scripts/smoke_n4.py` | أخضر (طلاب/قالب ← تعارض قاعة ← حصة ← إلغاء مؤرّخ ← درجة ← نشر ← منع 409 ← تصدير 5KB) |
| Flutter | `flutter analyze` / `flutter test` / `flutter build web --release` | 0 ملاحظات · **43/43** · بناء ناجح |
| لوحة التحكم | `npm run build` | ناجح (تحذير حزمة >500KB متوقع) · ثلاث شاشات وظيفية + تجربة يدوية لـ`ADMIN-001` |
| APK (release) | `flutter build apk --release` من `X:\app` (5.6) | **67.5MB · بناء ناجح متكرر** (موقّع بمفتاح debug) |
| git | `git log` | مستودع محلي + 3 التزامات · مدفوع للمستودع البعيد `JJ36t/csit-app` |
| CI | GitHub Actions | ✅ **نجح فعلياً من أول تشغيل** — 3/3 وظائف (API على PostgreSQL 16 + Flutter + لوحة التحكم) |

**غير متحقق (اذكره دائماً):** تثبيت APK وتجربة الكاميرا والماسح على جهاز حقيقي (البناء وحده لا يثبت عمل الكاميرا)، وبناء iOS (يحتاج macOS).

---

## 4) خريطة الملفات المهمة

```
csit-app/
├── README.md                  ← ملخص المشروع وحالة التحقق
├── HANDOFF.md                 ← هذا الملف
├── api/
│   ├── app/
│   │   ├── config.py          ← كل الإعدادات (JWT، QR، السماحية، الحرم، bcrypt الاستيراد)
│   │   ├── db.py · deps.py · errors.py · schemas.py · security.py
│   │   ├── main.py            ← تسجيل كل الموجّهات
│   │   ├── models/            ← base, enums(SAEnum), identity, academic, timetable, attendance, content, comms
│   │   ├── routers/           ← auth, admin_users, admin_students, admin_timetable, attendance, timetable,
│   │   │                        departments, health, grades, materials, announcements, notifications
│   │   └── services/          ← attendance(QR/مسافة), access, audit, import_students, rate_limit, sessions,
│   │                            storage(ملفات), file_links(روابط موقّعة), notifications(جمهور/إشعارات)
│   ├── migrations/versions/   ← 0001_initial_schema · 0002_device_unique_active · 0003_materials_announcements
│   ├── scripts/               ← seed, create_admin, reset_device, import_students, inspect_db, smoke_e2e,
│   │                            demo_seed, smoke_n3
│   └── tests/                 ← world.py (عالم اختباري) + 8 ملفات اختبار
├── app/  (Flutter)
│   └── lib/  ← main, app/router, core/{network/{api_client,authed_dio},storage,utils,
│              features/auth{data,presentation}, features/home,
│              features/attendance/{data/{attendance_api,qr_payload,location_service,
│                attendance_scanner}, presentation/{scan_page,sessions_page,live_session_page}},
│              l10n/app_ar.arb
├── admin/ (React + Vite + AntD)
│   └── src/  ← App.tsx, api.ts, pages/{LoginPage, StudentsPage, TimetablePage, GradesPage}
└── design/screens.html
```

**نقاط الـAPI الحالية:** `health` · `auth/{login,refresh,logout,change-password,me}` · `departments` · `offerings` · `admin/students/{import,template,list}` · `admin/users/{id}/{device/reset,reset-password}` · `sessions/{id}/{open,close,live}` · `attendance/{scan,summary}` · `attendance/{id}` (PATCH) · `offerings/{id}/attendance{,/report}` · `timetable` · `timetable/changes` · `admin/timetable/{rooms,slots,changes}` · `assessments` · `assessments/{id}/{grades,publish}` · `offerings/{id}/grades{,/export}` · `grades` · `offerings/{id}/materials` · `materials/{id}` · `files/{id}/download` · `admin/announcements` · `announcements` · `announcements/{id}/read` · `notifications{,/{id}/read,/read-all}` · `devices/fcm-token`.

---

## 5) كيف تشغّل وتتحقق (أوامر جاهزة على هذا الجهاز)

### 5.1 تهيئة الجلسة (Windows / PowerShell 5.1)
جلسة الأوامر في هذه البيئة تنقصها متغيّرات نظام قياسية، وFlutter وpsql ليسا على PATH:

```powershell
$env:SystemRoot='C:\Windows'; $env:ProgramFiles='C:\Program Files'; ${env:ProgramFiles(x86)}='C:\Program Files (x86)'
$env:ProgramData='C:\ProgramData'; $env:ComSpec='C:\Windows\System32\cmd.exe'
$env:TEMP='C:\Windows\Temp'; $env:TMP='C:\Windows\Temp'
$env:LOCALAPPDATA=Join-Path $env:USERPROFILE 'AppData\Local'
$env:APPDATA=Join-Path $env:USERPROFILE 'AppData\Roaming'
$env:PUB_CACHE=Join-Path $env:LOCALAPPDATA 'Pub\Cache'
$env:Path="C:\Users\hmt1\develop\flutter\bin;C:\Windows\System32;C:\Windows;"+$env:Path
```

- **Flutter**: `C:\Users\hmt1\develop\flutter\bin\flutter.bat` (3.47.8 · Dart 3.13.7).
- **PostgreSQL 18.6**: خدمة `postgresql-x64-18` على 5432، وأدواته في `C:\Program Files\PostgreSQL\18\bin` (ليس على PATH). قاعدتا `csit` (تطوير) و`csit_test` (اختبار).
- **كلمة مرور `postgres`**: يزوّدك بها المستخدم عند الحاجة — **لا تُكتب في أي ملف ولا في git**.

### 5.2 الخلفية
```powershell
cd csit-app/api
python -m pip install -r requirements-dev.txt
$env:DATABASE_URL='sqlite:///./test_api.db'; python -m pytest tests -q          # 43/43
$env:DATABASE_URL='postgresql+psycopg://postgres:<PW>@127.0.0.1:5432/csit_test'; python -m pytest tests -q
$env:DATABASE_URL='postgresql+psycopg://postgres:<PW>@127.0.0.1:5432/csit'
python -m alembic upgrade head; python -m alembic check
python -m uvicorn app.main:app --port 8000      # http://localhost:8000/docs
```

### 5.3 الفحص الشامل عبر HTTP
```powershell
cd csit-app/api
python scripts/create_admin.py ADMIN-001 "مدير الكلية" "Admin#2026"
$p = Start-Process python -ArgumentList '-m','uvicorn','app.main:app','--port','8123','--log-level','warning' -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 7
python scripts/smoke_e2e.py
Stop-Process -Id $p.Id -Force
```

### 5.4 تطبيق Flutter
```powershell
cd csit-app/app
flutter pub get; flutter gen-l10n; flutter analyze; flutter test; flutter build web --release
```

### 5.5 لوحة التحكم
```powershell
cd csit-app/admin; npm ci; npm run build
```

### 5.6 بناء APK (Android SDK مثبّت — والمشكلة: المسار طويل)
مسار هذه المساحة ~160 حرفاً، ومسار مجلد البناء يتجاوز حد ويندوز 260 حرفاً فيفشل
`aot_android_asset_bundle` (خط `CupertinoIcons.ttf`). **الحل المجرَّب:** اربط المساحة بقرص قصير وابنِ منه:
```powershell
subst X: <مسار csit-app المطلق>
cd X:\app; flutter build apk --release
```
مع الإعدادين الموجودين في `app/android/gradle.properties`:
`kotlin.incremental=false` و`kotlin.compiler.execution.strategy=in-process`
(بلا هما يفشل Kotlin daemon بـ«different roots» عند تغيير جذر المسار).
الناتج: `X:\app\build\app\outputs\flutter-apk\app-release.apk` — موقّع بمفتاح debug (للتجربة لا للنشر).
البديل عند تعذّر `subst`: نسخة على `C:\csit-build` بنفس الأوامر.

### 5.7 تشغيل الخدمات محلياً (عرض حي)
```powershell
# 1) قاعدة البيانات + بيانات العرض
cd api; $env:PGPASSWORD='<PW>'; $env:DATABASE_URL='postgresql+psycopg://postgres@127.0.0.1:5432/csit'
python -m alembic upgrade head; python scripts/seed.py; python scripts/demo_seed.py
python scripts/create_admin.py ADMIN-001 "مدير الكلية" "Admin#2026"
# 2) الـAPI
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# 3) لوحة التحكم (نافذة أخرى) — proxy /api إلى 8000
cd admin; npm run dev            # http://localhost:5173
# 4) تطبيق الويب (نافذة أخرى)
cd X:\app; flutter build web --release --dart-define=API_BASE_URL=http://127.0.0.1:8000
cd build\web; python -m http.server 8080 --bind 127.0.0.1   # http://127.0.0.1:8080
```
حسابات العرض: تدريسي `T-100` / طالب `S-100` / مدير `ADMIN-001` — كلمة المرور للأولين `Test#12345` وللمدير `Admin#2026`.

**«هذا الحساب مرتبط بجهاز آخر»:** قاعدة الجهاز النشط الواحد؛ كل متصفح/هاتف = بصمة مختلفة. للتصفير في التطوير:
```powershell
cd api; python scripts/dev_reset_devices.py        # الجميع
cd api; python scripts/dev_reset_devices.py S-100  # حساب واحد
```
ثم الدخول من الجهاز الجديد يربطه تلقائياً. استخدم رابطاً واحداً ثابتاً للتطبيق (`http://127.0.0.1:8080` وليس `localhost`) لأن كل أصل (origin) يُعدّ بصمة جديدة.

---

## 6) الفخاخ المعروفة — اقرأها قبل التعديل

1. **أنواع Enum على PostgreSQL**: `downgrade` في `0001` يُسقط الأنواع عبر قائمة `_PG_ENUMS`. أي نوع Enum جديد يُضاف لاحقاً **يجب** إضافته لتلك القائمة وإلا فشلت إعادة الترقية بـ«النوع موجود مسبقاً».
2. **القوائم تُخزَّن بقيمها الصغيرة** عبر `app.models.enums.SAEnum` (values_callable). لا تستخدم `sa.Enum` مباشرة في النماذج.
3. **معرّفات UUID في الاختبارات**: مرّر `uuid.UUID(...)` لا نصاً عند `db.get(...)` أو المقارنات، وإلا ظهر `'str' object has no attribute 'hex'`.
4. **SQLite يعيد تواريخ بلا منطقة زمنية** → استخدم `app.security.as_utc()` قبل أي مقارنة.
5. **تهيئة الاختبارات على PostgreSQL**: `conftest._reset_schema()` يُسقط أنواع Enum بعد `drop_all` (لأن `drop_all` لا يفعلها).
6. **مسارات أطول من 260 حرفاً**: لا يفتحها Python على ويندوز. استخدم بادئة `\\?\` مع المسار المطلق (هكذا قُرئ ملف الخطة المرفق). **ونفس القيد يضرب بناء APK**: مسار هذه المساحة ~160 حرفاً، ومسارات `build/app/intermediates/flutter/release/flutter_assets/...` تتجاوز 260 فتسقط كتابة الخطوط بـ`IconTreeShakerException`. **الحل النهائي المجرَّب:** `subst X: <المساحة>` والبناء من `X:\app` (5.6).
7. **PowerShell 5.1**: `>` ينتج UTF‑16؛ لا تعتمد عليه لملفات UTF‑8. والأفضل كتابة سكربتات Python بدل حشو JSON في سطر الأوامر.
8. **ملفات المصدر العربية**: عند التعديل بمطابقة نص عربي قد تفشل المطابقة بسبب التشكيل الخفي — استخدم مرساة إنجليزية (سطر `import ...` مثلاً).
9. **Flutter في هذه البيئة**: يحتاج `LOCALAPPDATA` و`PUB_CACHE` (وإلا «Could not find the pub cache»)، و`${env:ProgramFiles(x86)}` لأمر `flutter test`.
10. **لا Android SDK**: `flutter build apk` سيفشل. التحقق المتاح: `analyze` + `test` + `build web`.
11. **الاستيراد الجماعي**: كلمات المرور الأولية تُجزَّأ بكلفة bcrypt 10 (`import_bcrypt_rounds`) وتُغيَّر إجبارياً عند أول دخول.
12. **حدّ المحاولات في الذاكرة**: نسخة خدمة واحدة؛ عند التوسع يُستبدل بـRedis دون تغيير الواجهة (`app/services/rate_limit.py`).
13. **mobile_scanner 7.x**: الواجهة `MobileScannerController.barcodes` + `MobileScanner(controller:, fit:)`؛ غلافنا `features/attendance/data/attendance_scanner.dart` يُحقن بماسح وهمي في الاختبارات (لا كاميرا).
14. **ListView في الاختبارات يبني أبناءه بكسل**: البطاقات أسفل النافذة غير موجودة في الشجرة (فشل `findsOneWidget` زوراً أو `pumpAndSettle` معلّق على مؤشر). اضبط `tester.view.physicalSize` (مثل 390×1000 منطقية) في كل اختبار شاشة.
15. **لا تقرأ `AppLocalizations.of(context)` في `initState`**: يُرمى assertion أثناء التهيئة ويبقى المؤشر دوّاراً إلى الأبد. اقرأ الترجمة بعد `await` مع فحص `mounted`.
16. **ARB بمعاملات**: كل مفتاح بمعامل يحتاج `@key.placeholders` وإلا يفشل `flutter gen-l10n`؛ والأعداد من نوع `int`.
17. **خطوط Cupertino**: `flutter build web` يحذّر إن لم تضف `cupertino_icons` (mobile_scanner يشير إلى أيقوناتها) — أُضيفت.
18. **Kotlin daemon بعد تغيير جذر المسار** (subst/نسخة): يفشل بـ«Could not close incremental caches … different roots». الحل المثبت في `android/gradle.properties`: `kotlin.incremental=false` + `kotlin.compiler.execution.strategy=in-process`، وبعدها `gradlew --stop` مرة واحدة إن بقي كاش قديم.
19. **git غير مدرج على PATH** في هذه البيئة: استخدم `C:\Program Files\Git\cmd\git.exe` مباشرة (أو `$env:Path += ';C:\Program Files\Git\cmd'`).
20. **سكربتات `smoke_*` تربط جهازاً للحساب** (قاعدة الجهاز الواحد): بعد تشغيلها يفشل دخول المدير من المتصفح بـ«مرتبط بجهاز آخر». الحل: `python scripts/dev_reset_devices.py` ثم الدخول من جديد.

---

## 7) الخطوات التالية بالترتيب (مع معايير قبول)

### N1 — تطبيق Flutter: شاشة المسح والحاضرين — ✅ منجز (26 ت10 2026)
- أُنجز: شاشة مسح تقرأ الرمز وترسل `POST /attendance/scan` بـ`device_id` (المحفوظ عند الدخول) + الموقع من `geolocator` (اختياري)؛ بطاقة نتيجة (حاضر/متأخر/مشكوك مع السبب)؛ شاشة «حصص اليوم» للتدريسي؛ قائمة حاضرين لحظية تقرأ `/sessions/{id}/live` بتحديث دوري (10 ثوانٍ) مع فتح/إغلاق الجلسة وQR متجدد.
- القبول متحقق: `flutter analyze` صفر ملاحظات · **27/27** اختباراً (منها 17 للحضور ببدائل في الذاكرة) · لا نصوص عربية في الكود (كلها في `app_ar.arb`) · لا تعديل على الـAPI (43/43 على القاعدتين قبل التنفيذ وبعده).
- صيغة رمز QR المعروض: `csit:v1:<session_id>:<token>` — موثقة في `qr_payload.dart`، وأي شاشة عرض رمز مستقبلية تستخدمها.
- المتبقي: تثبيت APK وتجربة الكاميرا والمسح على هاتف حقيقي (لا يُثبتها البناء) — تُجرَّب في الاعتماد التجريبي N7.
- **APK:** بُني بنجاح أول مرة (66.5MB، موقّع debug) — يُعاد بناؤه من مسار قصير كما في 5.6.

### N3 — الـAPI: المواد والإعلانات والإشعارات والدرجات — ✅ منجز (26 ت10 2026)
- أُنجز: التقييمات وإدخال الدرجات الدفعي (مسودة) والنشر بموافقة مدير الكلية مع تدقيق كل تعديل وإشعار المسجَّلين، ومصفوفة درجات المادة وتصدير Excel، والمواد (رفع PDF/رابط + تنزيل برابط موقّع 10 دقائق)، والإعلانات بخمسة نطاقات وجدولة نشر وعلامة مقروء، وصندوق الإشعارات و`fcm-token`.
- القبول متحقق: 19 اختباراً جديداً (المطلوب ≥12) → **62/62** على SQLite وPostgreSQL · `alembic check` نظيف بعد الترحيل 0003 · كل إدخال/تعديل درجة ونشر مسجَّل في `audit_logs` · `smoke_n3` أخضر عبر HTTP.
- ملاحظة: الإرسال الفعلي عبر FCM مؤجّل (يُخزَّن الرمز فقط) كما في الخطة.

### N2 — تطبيق Flutter: الجدول والمواد والدرجات — ✅ منجز (26 ت10 2026)
- أُنجز: شاشة جدول بأيام وشرائح بتوقيت بغداد + لافتة تغييرات مؤرخة + **قراءة من ذاكرة محلية** عند تعذر الشبكة (shared_preferences)؛ شاشة المواد (مواد المستخدم من `GET /offerings` ← ملفاتها)، وفتح PDF برابط موقّع/روابط الفيديو عبر `url_launcher`؛ شاشة الدرجات (المنشور فقط + المجموع الموزون).
- القبول متحقق: `flutter analyze` صفر ملاحظات · **43/43** اختباراً (16 جديدة) · لا نصوص عربية في الكود · يعمل بلا إنترنت للجدول (ذاكرة محلية).
- إضافة API مرافقة: `GET /offerings` + `offering_id` في عناصر `/timetable` (3 اختبارات → 65/65).

### N3 — الـAPI: المواد والإعلانات والإشعارات والدرجات — ✅ منجز (26 ت10 2026)
- أُنجز: التقييمات وإدخال الدرجات الدفعي (مسودة) والنشر بموافقة مدير الكلية مع تدقيق وإشعار المسجَّلين، ومصفوفة درجات المادة وتصدير Excel، والمواد (رفع PDF/رابط + تنزيل برابط موقّع)، والإعلانات بخمسة نطاقات وجدولة، وصندوق الإشعارات و`fcm-token`.
- القبول متحقق: 19 اختباراً جديداً · `alembic check` نظيف بعد الترحيل 0003 · كل إدخال/نشر مدقَّق · `smoke_n3` أخضر.
- **قبول:** اختبارات ≥12 حالة جديدة، `alembic check` نظيف، كل تعديل درجة/نشر مدقَّق، والاختبارات تمر على القاعدتين.

### N4 — لوحة التحكم: ثلاث شاشات وظيفية — ✅ منجز (26 ت10 2026)
- أُنجز: الطلاب (قائمة + استيراد بمرحلتين + تقرير أخطاء عربي + أقسام من الـAPI)، الجدول (حصص في نطاق + تغييرات + خطة أسبوعية + إدارة قاعات/حصص/تغييرات مع عرض التعارض)، الدرجات (تقييمات وأوزان + مصفوفة إدخال دفعي + حفظ مسودة + نشر مقصور على مدير الكلية + تصدير Excel).
- **قبول متحقق:** `npm run build` ناجح · تجربة يدوية حيّة بحساب `ADMIN-001` على المسارات الثلاثة · أخطاء الخادم تُعرض بالعربية (`message_ar` + رمز) · لا كلمة مرور في الكود · `smoke_n4.py` أخضر · اختبارات API **69/69**.
- **ما لم يُتحقق:** اختبار اللوحة على متصفح سطح مكتب عريض (جرِّبت على لوحة عرض ضيقة ~488px)؛ تنزيل Excel من زر الواجهة (التحقق تم على مستوى HTTP).
- **قيود معروفة:** (1) `GET /admin/timetable/slots` يعرض حصص كل الفصول لأن `timetable_slots` بلا `term_id` — يُرشّح لاحقاً عند تعدد الفصول. (2) كلمات مرور حسابات العرض مكتوبة في سكربتات `smoke_*` و`demo_seed.py` عمداً (بيانات تطوير محلية) — لا تُستخدم في الإنتاج.

### N5 — التشغيل والصلابة
- Redis لحدّ المحاولات والكاش (واجهة جاهزة في `services/rate_limit.py`).
- نسخ احتياطي آلي + فحص استرجاع شهري (سكربت + توثيق).
- `docker-compose.yml` للنشر على سيرفر الجامعة + Nginx/Caddy + HTTPS + `/health`.

### N6 — Git وCI — ✅ منجز (26 ت10 2026)
- ✅ `git init -b main` + أول التزام `f621fda` (166 ملفاً، بلا مخرجات بناء).
- ✅ رفع إلى GitHub: `https://github.com/JJ36t/csit-app` (‏`git push -u origin main`).
- ✅ **CI نجح فعلياً** في أول تشغيل: الوظائف الثلاث خضراء (API على PostgreSQL 16 + SQLite، Flutter 3.47.8 analyze/test/build web، لوحة التحكم npm ci+build).
- ملاحظة: المستودع عام — يُنصح بتحويله خاصاً قبل إدخال بيانات طلاب حقيقية.

### N7 — الاعتماد التجريبي (المرحلة 6 من الخطة)
- شعبة واحدة لأسبوعين، درجات مادة واحدة، 20 مختبِراً في Play المغلقة (14 يوماً)، ثم تقرير أخطاء وتحسينات.

---

## 8) ما ينتظر المستخدم (بنود لا تُنجَز من طرفنا)

1. **قواعد الغياب والتأخير الرسمية** (حد التأخير، حد الإنذار/الحرمان، سياسة الأعذار) — تُملأ كإعدادات دون تعديل كود.
2. **الجدول الرسمي** للمحاضرات لكل قسم/مرحلة/شعبة (صباحي ومسائي)، والدرجات النهائية للتقييمات (أوزان، درجات عظمى).
3. **اسم مسؤول البيانات** الذي يزوّد ملفات الطلاب والجداول.
4. **الموافقة الكتابية** من العمادة على استخدام بيانات الطلاب الحقيقية (قبل أي استيراد حقيقي).
5. **تفاصيل السيرفر الجامعي** بعد لقاء وحدة تقنية المعلومات: المواصفات، نظام التشغيل، صلاحيات النشر، النطاق الفرعي، شهادة HTTPS، سياسة النسخ الاحتياطي.
6. **تأكيد الاسم الظاهر** «علوم الحاسوب» مع العمادة قبل النشر (المعرّف `iq.edu.qu.csit` نهائي).

---

## 9) قواعد العمل في هذا المشروع (لا تتجاوزها)

- **لا تسليم بلا تشغيل:** شغّل الاختبارات على القاعدتين، و`alembic check`، و`flutter analyze/test` قبل أي ادعاء نجاح. واذكر صراحةً ما لم تتحقق منه.
- **الاختبارات ليست شكلية:** لا تحذف اختباراً ولا تُضعف تأكيداً لتمرير بناء.
- **النصوص العربية في التطبيق** من `lib/l10n/app_ar.arb` فقط، والاتجاه RTL بأدوات `Directional`.
- **القيم النصية للقوائم** صغيرة (`present`, `morning`)، والوقت يُخزَّن UTC ويُعرض بتوقيت بغداد.
- **كل تعديل حساس** (حضور، درجة، جهاز، كلمة مرور، استيراد) يمر عبر `audit_logs`.
- **الوثائق عربية**، وأسماء ملفات التسليم عربية عند الحاجة.
- **الأمان:** لا تكتب كلمات مرور أو مفاتيح في الملفات؛ `JWT_SECRET` يُمرَّر عبر البيئة على السيرفر.

---

## 10) برومبت جاهز للحساب الجديد

> اقرأ `csit-app/HANDOFF.md` كاملاً، ثم افحص حالة المستودع الفعلية (لا تعتمد على ذاكرة سابقة)، وشغّل اختبارات الـAPI على SQLite وPostgreSQL و`flutter analyze`/`flutter test` لتأكيد الحالة. بعدها ابدأ من «الخطوات التالية» في القسم 7 — **N5 (التشغيل والصلابة: Redis + نسخ احتياطي + docker-compose/Nginx)** — وأبلغني بما تحققت منه وما لم يتحقق.

---

### سجل التغييرات المختصر
- **25 ت10 2026:** المرحلة 1 (29 جدولاً + الأقسام + لوحة أولية) والمرحلة 2 (مصادقة + استيراد + تدقيق) — 27 اختباراً على القاعدتين.
- **26 ت10 2026:** المرحلة 3 (حضور QR + جدول + تعارضات + فهرس جزئي + CI) — **43 اختباراً** على القاعدتين، ونموذج الشاشات الثماني.
- **26 ت10 2026 (تكملة):** N1 — الحضور في Flutter (مسح QR للطالب + قائمة لحظية وQR متجدد للتدريسي) — **27/27** اختبار واجهة، `analyze` نظيف، `build web` ناجح، **أول APK ناجح (66.5MB)**، وإعادة إنشاء `ci.yml` المفقود.
- **26 ت10 2026 (N2):** الجدول والمواد والدرجات في Flutter + `GET /offerings` — **43/43** اختبار واجهة و**65/65** على القاعدتين، وAPK 67.5MB.
- **26 ت10 2026 (GitHub):** رفع المستودع إلى `JJ36t/csit-app` — **CI أخضر 3/3 من أول تشغيل فعلي**.
- **26 ت10 2026 (N4):** شاشات لوحة التحكم الثلاث (طلاب/جدول/درجات) + `GET /admin/timetable/{rooms,slots}` و`slot_id` في `/timetable` — **69/69** على SQLite، `npm run build` ناجح، `smoke_n4` أخضر، وتجربة يدوية بحساب `ADMIN-001`.
