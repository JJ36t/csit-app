# حالة المشروع وخطة المتابعة — تطبيق كلية علوم الحاسوب وتكنولوجيا المعلومات

> **لمن يقرأ هذا الملف:** أنت تكمل عملاً جارياً. اقرأ الملف كاملاً قبل أول تعديل، ثم نفّذ «الخطوات التالية» بالترتيب.
> لا تعِد بناء ما هو مكتمل، ولا تعلن نجاح شيء لم تشغّله فعلاً.
> آخر تحديث: **الاثنين 26 تشرين الأول 2026**.

---

## 0) ابدأ من هنا — خلاصة في عشرة أسطر

1. المشروع: تطبيق أندرويد لكلية علوم الحاسوب وتكنولوجيا المعلومات — جامعة القادسية، بخلفية FastAPI/PostgreSQL ولوحة تحكم ويب.
2. المستودع: `csit-app/` وفيه `api/` و`app/` (Flutter) و`admin/` (React) و`design/` (نموذج الشاشات).
3. **مكتمل ومتحقَّق منه:** المصادقة وربط الجهاز، استيراد الطلاب من Excel، الحضور (QR متجدد + موقع + لحظي + تقارير)، الجدول (حصص + تعارضات + تغييرات مؤرخة)، فهرس «جهاز نشط واحد»، ودرجات ومواد وإعلانات وإشعارات (N3)، وملف CI.
4. الحالة الحالية للاختبارات: **94/94 على SQLite و94/94 على PostgreSQL** (الترحيلات 0001–0004)، و`alembic check` نظيف، و`smoke_n4` أخضر، ودورة نسخ/استرجاع مُجرَّبة، و**Redis حقيقي** و**حزمة Docker** مُختبَران، وFlutter **65/65**.
5. تطبيق Flutter: المصادقة + **N1 الحضور** + **N2 الجدول والمواد والدرجات** + **الإعلانات والإشعارات والملف الشخصي** + **APK ناجح** (67.8MB)؛ ولوحة التحكم: سبع شاشات مكتملة، والـAPI يخدمها كلها.
6. **التالي فوراً:** N7 — الاعتماد التجريبي (شعبة واحدة لأسبوعين، 20 مختبِراً في Play المغلقة). لوحة التحكم اكتملت بشاشاتها السبع. متبقٍّ من النشر: شهادة HTTPS فقط (تنتظر سيرفر الجامعة).
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

**المرحلة 8 — N5: التشغيل والصلابة (26 ت10 2026):**
- **حدّ المحاولات:** Redis بـINCR+EXPIRE عند `REDIS_URL`، ورجوع آلي بتحذير واحد إلى عدّاد الذاكرة عند أي عطل،
  وربط `auth.py` بالخدمة (كان يحمل عدّاداً مكرراً لا يغطيه Redis). الواجهة `guard/record/clear` كما هي.
- **نسخ احتياطي واسترجاع:** سكربتان جديدان + `api/backups/` في `.gitignore`؛ الدورة الحقيقية نجحت على PostgreSQL.
- **حزمة النشر:** `docker-compose.yml` + `api/Dockerfile` + `admin/Dockerfile` + `admin/nginx.conf` + `.env.example`
  (PostgreSQL 16، API يرقّي المخطط قبل الإقلاع، Nginx يخدم SPA ويوجّه `/api` و`/health`).
- **`/health`:** يفحص `SELECT 1` ويقرأ `alembic_version`، ويعيد 503 `degraded` عند تعطّل القاعدة.
- **اختبارات جديدة:** 5 للخدمة (بعميل وهمي) + 4 لمسار Redis (fakeredis) + 3 لـ`/health` → **80/80** على القاعدتين.

**المرحلة 9 — بقية شاشات اللوحة: الإعلانات والمستخدمون وسجل التدقيق والملخص (26 ت10 2026):**
- **الإعلانات:** `GET /admin/announcements` يعيد المجدولة والمنتهية مع `status` محسوبة (scheduled/active/expired)
  ونطاق رئيس القسم (الكلية + قسمه)؛ وشاشة إنشاء/حذف بنطاق كلية/قسم/مرحلة/مادة وجدولة نشر وانتهاء.
- **المستخدمون:** `GET /admin/users` (بحث/دور/قسم/ترقيم، بلا أي سر) مع `device_status`، وشاشة إجراءات:
  إعادة ضبط الجهاز وكلمة المرور المؤقتة تُعرض مرة واحدة (Modal + نسخ).
- **سجل التدقيق:** ترحيل `0004` يضيف `audit_logs.created_at` (server_default now)، و`GET /admin/audit`
  (مدير الكلية فقط) بترشيح الفاعل/الإجراء/الكيان/المدى الزمني بتوقيت بغداد، وشاشة بصف موسّع يعرض before/after.
- **لوحة الملخص:** `GET /admin/overview` بأرقام الطلاب وتوزيعهم وجلسات اليوم وحضورها وتقييمات منشورة/مسودات
  وإعلانات نشطة/مجدولة، محصورة بقسم رئيس القسم.
- **التحقق:** **93/93** على القاعدتين (13 اختباراً جديداً) · `alembic upgrade 0003→0004` + `check` نظيف على PostgreSQL ·
  `npm run build` ناجح · تجربة يدوية للشاشات الأربع بحساب `ADMIN-001`.

**المرحلة 10 — تطبيق Flutter: الإعلانات والإشعارات والملف الشخصي (26 ت10 2026):**
- **الإعلانات:** قائمة موجّهة من `GET /announcements` (تثبيت/أولوية/غير مقروء)، وفتح الإعلان يعلّمه مقروءاً
  عبر `POST /announcements/{id}/read`، مع تمرير للتحديث وحالات فراغ/خطأ.
- **الإشعارات:** صندوق وارد من `GET /notifications` بعدّاد غير مقروء، وتعليم واحد/الكل، وشارة على بطاقة الرئيسية
  تُحدَّث بعد العودة من الشاشة.
- **الملف الشخصي:** شاشة تعرض الاسم/الرقم/الدور/القسم/المرحلة/الشعبة، وروابط تغيير كلمة المرور والخروج.
- **البنية:** `features/announcements`, `features/notifications`, `features/profile_settings` بنمط data/presentation،
  وحقن عبر `AppServices`، وكل النصوص في `app_ar.arb` (تم فحص عدم وجود نص عربي داخل الودجات).
- **التحقق:** `flutter analyze` 0 ملاحظات · **65/65** اختباراً (22 جديداً) · `flutter build web --release` ناجح ·
  **APK 67.8MB** · إصلاح اختبار جدول كان يعتمد على `DateTime.now()` فيعبر منتصف الليل (ثُبّت على صباح اليوم ببغداد).

**المرحلة 11 — نشر بلا Docker (26 ت10 2026):**
- `deploy/systemd/`: خدمة `csit-api` (مستخدم غير جذري، `EnvironmentFile` بصلاحية 600، تصلّب بسيط) +
  مؤقّت نسخ احتياطي يومي ومؤقّت فحص استرجاع شهري.
- `deploy/nginx/csit.conf`: يخدم `admin/dist` مع SPA fallback ويعكس `/api/` و`/health`، وحد رفع 30MB.
- `deploy/DEPLOY.md`: خطوات كاملة حتى TLS و`curl /health` والنسخ الاحتياطي والاسترجاع.
- **التحقق:** مراجعة ملفية للاتساق والمسارات فقط (لا systemd ولا Nginx على ويندوز) — التنفيذ الفعلي ينتظر السيرفر.

**المرحلة 12 — تحقق بيئي: Redis حقيقي + محاولة Docker + إصلاح ترحيل 0004 (26 ت10 2026):**
- **Redis حقيقي:** نُزِّل بناء Windows المحمول (5.0.14.1) وعمل على 127.0.0.1:6379 بإعداد `api/redis-dev.conf`
  (بلا حفظ، استماع محلي فقط). `scripts/check_redis.py` أخضر، وهجوم دخول حقيقي: 5 محاولات 401 ثم **429**،
  والمفتاح `ratelimit:ADMIN-001|127.0.0.1` في Redis بـTTL، والدخول الصحيح بعدها **صفّر المفتاح**.
- **Docker:** ثُبِّت Docker Desktop عبر winget (CLI 29.9.2 · Compose 5.6.1) و`docker compose config` يتحقق
  من الملف (3 خدمات، تعويض المتغيّرات، المنافذ). **المحرّك لا يعمل**: خدمة `com.docker.service` تتطلب مديراً،
  وWSL2 (وHyper-V) غير مفعّلين على الجهاز — لذا لم يُبنَ أي image ولم يُشغَّل `up`.
- **عيب حقيقي أُصلح:** ترحيل `0004` كان يفشل على SQLite إذا كان الجدول فيه صفوف
  («Cannot add a column with non-constant default»)، لأن SQLite يرفض `DEFAULT CURRENT_TIMESTAMP` في
  `ADD COLUMN`. صار الترحيل يستخدم `batch_alter_table` على SQLite فقط، مع **اختبار انحدار** يبني قاعدة على
  `0003` ويُدخل صفاً ثم يرقّي — ويمرّ الآن على SQLite وPostgreSQL.

**المرحلة 13 — تشغيل حزمة Docker والتحقق منها (26 ت10 2026):**
- بعد تثبيت WSL 3.0.3 + VirtualMachinePlatform وإعادة التشغيل، صار محرّك Docker 29.9.2 يعمل،
  وبُنيت الصورتان (`csit-app-api` 333MB · `csit-app-admin` 75.3MB) وارتفعت الخدمات الثلاث healthy.
- **`/health` عبر Nginx** (8080): `{"status":"ok","database":"ok","revision":"0004"}`، وعند إيقاف القاعدة:
  **503** `{"status":"degraded","database":"unavailable"}` ثم عاد 200 بعد تشغيلها.
- **الاستمرارية:** أُوقف/أُعيد تشغيل `api` فبقي الملف المرفوع قابلاً للتنزيل بنفس الرابط الموقّع (volume uploads).
- **نسخ/استرجاع في وضع compose:** `deploy/backup-compose.ps1 -Verify` — نسخة 86.4KB، استرجاع لقاعدة مؤقتة،
  تطابق `users/attendance_records/grades/assessments`، ثم حذف المؤقتة.
- **الواجهة عبر Nginx:** الصفحة والأصول 200، ودخول `ADMIN-001` من المتصفح عرض أرقام لوحة الملخص الحقيقية.
- **سكربت الفحص:** `deploy/compose-smoke.ps1` (تشغيل المحرّك + build + زرع + دخول + ملخص + صفحة).

---

## 3) حالة التحقق الحالية (أرقام حقيقية — أعدها قبل أي تسليم)

| الفحص | الأمر | النتيجة عند كتابة الملف |
|---|---|---|
| اختبارات API على SQLite | `pytest tests -q` | **94/94** |
| اختبارات API على PostgreSQL 18.6 | `DATABASE_URL=postgresql+psycopg://…` | **94/94** |
| مسار Redis لحدّ المحاولات | `pytest tests/test_rate_limit_redis.py` | **4/4** بـfakeredis (لا خدمة Redis على الجهاز) |
| الترحيلات على PostgreSQL | `alembic upgrade head` + `alembic check` | 0001–0004 · «No new upgrade operations detected» |
| دورة الإرجاع | `alembic downgrade base` ثم `upgrade head` | نظيفة |
| فحص HTTP شامل | `python scripts/smoke_e2e.py` | أخضر (مدير ← استيراد ← طالب ← منع جهاز ← إعادة ضبط ← رفض صلاحيات) |
| فحص N3 عبر HTTP | `python scripts/smoke_n3.py` | أخضر (تقييم ← درجة ← نشر ← درجة الطالب ← إعلان/إشعار ← مادة برابط موقّع) |
| فحص N4 عبر HTTP | `python scripts/smoke_n4.py` | أخضر (طلاب/قالب ← تعارض قاعة ← حصة ← إلغاء مؤرّخ ← درجة ← نشر ← منع 409 ← تصدير 5KB) |
| نسخ احتياطي + استرجاع | `backup_db.py` ثم `verify_restore.py` | نسخة 94.6KB ← استرجاع بلا أخطاء ← تطابق 5/0/1 ← `0003 (head)` ← حذف القاعدة المؤقتة |
| `/health` حيّاً على PostgreSQL | `GET /health` | 200 · `{"status":"ok","database":"ok","revision":"0003"}` |
| تجربة يدوية للشاشات الأربع الجديدة | `ADMIN-001` على خدمة حيّة | الملخص (3 طلاب/جلسة/تقييمان) · إعلان يُنشأ ثم يُحذف · 5 مستخدمين + كلمة مرور مؤقتة تُعرض مرة · تدقيق بأوقات بغداد وترشيح `password_reset` = سجل واحد |
| حزمة Docker | `docker compose up -d --build` + `deploy/compose-smoke.ps1` | ✅ **3 خدمات healthy** (db/api/admin) · `/health` عبر Nginx: 200 و`revision 0004` · 503 `degraded` عند إيقاف القاعدة · الملفات المرفوعة تبقى بعد `restart` · نسخ/استرجاع 86.4KB بأعداد مطابقة · لوحة التحكم تعمل على 8080 · الصور: api 333MB · admin 75.3MB |
| Redis فعلي (5.0.14.1 محلي) | `scripts/check_redis.py` + هجوم دخول حقيقي | ✅ عدّاد 2 · TTL 60s · حجب · تصفير؛ وخمس محاولات 401 ثم **429** بالعربية مع مفتاح `ratelimit:<رقم>|<ip>` في Redis |
| ترحيل 0004 على قاعدة فيها بيانات | SQLite (21 صفاً) + PostgreSQL (صف) | ✅ بعد إصلاح batch: العمود أُضيف، الصفوف حصلت على وقت، الفهارس باقية، و`downgrade` نظيف |
| Flutter | `flutter analyze` / `flutter test` / `flutter build web --release` | 0 ملاحظات · **65/65** · بناء ناجح |
| لوحة التحكم | `npm run build` | ناجح (تحذير حزمة >500KB متوقع) · ثلاث شاشات وظيفية + تجربة يدوية لـ`ADMIN-001` |
| APK (release) | `flutter build apk --release` من `X:\app` (5.6) | **67.8MB · بناء ناجح** بعد شاشات الإعلانات/الإشعارات/الملف الشخصي (موقّع debug) |
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
│   │   ├── routers/           ← auth, admin_users, admin_students, admin_timetable, admin_audit, admin_overview,
│   │   │                        attendance, timetable, departments, health, grades, materials, announcements,
│   │   │                        notifications
│   │   └── services/          ← attendance(QR/مسافة), access, audit, import_students, rate_limit, sessions,
│   │                            storage(ملفات), file_links(روابط موقّعة), notifications(جمهور/إشعارات)
│   ├── migrations/versions/   ← 0001_initial_schema · 0002_device_unique_active · 0003_materials_announcements ·
│   │                            0004_audit_created_at
│   ├── scripts/               ← seed, create_admin, reset_device, import_students, inspect_db, smoke_e2e,
│   │                            demo_seed, smoke_n3, smoke_n4, backup_db, verify_restore
│   └── tests/                 ← world.py (عالم اختباري) + 17 ملف اختبار
├── app/  (Flutter)
│   └── lib/  ← main, app/router, core/{network/{api_client,authed_dio},storage,utils,
│              features/auth{data,presentation}, features/home,
│              features/attendance/{data/{attendance_api,qr_payload,location_service,
│                attendance_scanner}, presentation/{scan_page,sessions_page,live_session_page}},
│              features/{announcements,notifications,profile_settings}/…, l10n/app_ar.arb
├── admin/ (React + Vite + AntD)
│   └── src/  ← App.tsx, api.ts, pages/{LoginPage, StudentsPage, TimetablePage, GradesPage,
│                          AnnouncementsPage, UsersPage, AuditPage, DashboardPage}
├── docker-compose.yml          ← db + api + admin(Nginx)
├── .env.example                ← متغيرات النشر (بلا أسرار)
├── api/Dockerfile · admin/Dockerfile · admin/nginx.conf
├── deploy/                     ← systemd + Nginx + DEPLOY.md (نشر بلا Docker)
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
$env:DATABASE_URL='sqlite:///./test_api.db'; python -m pytest tests -q          # 93/93
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
21. **SQLite يرفض `ADD COLUMN ... DEFAULT CURRENT_TIMESTAMP`** على جدول فيه صفوف: أي ترحيل يضيف عموداً بـ`server_default=func.now()` يجب أن يستخدم `op.batch_alter_table` على SQLite (انظر `0004` واختبار الانحدار).
22. **`docker` يكتب تقدّم البناء وتنبيهات الإضافات على stderr**: مع `$ErrorActionPreference='Stop'` في PowerShell 5.1 يُعامَل ذلك كخطأ يُنهي السكربت. الحل: `2>&1 | Out-Host` أو `2>$null` مع التحقق من `$LASTEXITCODE`. وسكربتات `.ps1` العربية تحتاج **UTF-8 BOM** وإلا فشل تحليلها في 5.1.

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

### N5 — التشغيل والصلابة — ✅ منجز (26 ت10 2026)
- **Redis لحدّ المحاولات:** تنفيذ INCR+EXPIRE عند ضبط `REDIS_URL`، ورجوع آلي إلى الذاكرة بتحذير واحد عند أي عطل،
  وربط `auth` بالخدمة بدل عدّاده الخاص. اختبارات: 5 للخدمة (بعميل وهمي) + 4 لمسار Redis (fakeredis).
- **نسخ احتياطي + فحص استرجاع:** `scripts/backup_db.py` (pg_dump -Fc إلى `api/backups/` المستثنى) و
  `scripts/verify_restore.py` (قاعدة مؤقتة + مقارنة `users/attendance_records/grades` + `alembic current` + حذف).
  الدورة نُفِّذت فعلاً: 94.6KB ← تطابق 5/0/1 ← `0003 (head)`.
- **حزمة النشر:** `docker-compose.yml` (PostgreSQL 16 + API + لوحة خلف Nginx) و`api/Dockerfile` (مستخدم غير root
  + HEALTHCHECK) و`admin/Dockerfile` متعدد المراحل و`admin/nginx.conf` و`.env.example`.
- **`/health` عميق:** `status` + `database` + `revision`، و503 `degraded` عند تعطّل القاعدة — مُتحقَّق حيّاً على
  PostgreSQL (200 · revision 0003) وعلى مسار الفشل باختبار.
- **قبول متحقق:** 80/80 على القاعدتين · `/health` حيّ · دورة نسخ/استرجاع كاملة · لا أسرار في الملفات.
- **متبقٍ:** TLS/Nginx على سيرفر الجامعة (يحتاج النطاق والشهادة وتفاصيل الوحدة فقط).
  Redis (5.0.14.1) وحزمة Docker (3 خدمات + نسخ/استرجاع) **متحقَّقان فعلياً** محلياً.

### بقية شاشات اللوحة (الإعلانات/المستخدمون/التدقيق/الملخص) — ✅ منجز (26 ت10 2026)
- الإعلانات (قائمة إدارية بالحالة + إنشاء/حذف) · المستخدمون (قائمة + إعادة ضبط جهاز/كلمة مرور) ·
  سجل التدقيق (ترحيل 0004 + ترشيح + قبل/بعد) · لوحة الملخص (أرقام حقيقية بنطاق القسم).
- **قبول متحقق:** 93/93 على القاعدتين · بناء اللوحة ناجح · تجربة يدوية للأربعة · لا أسرار في الاستجابات.
- **ملاحظة نطاق:** سجل التدقيق لمدير الكلية فقط؛ رئيس القسم يحصل على 403 عربية.
- **متبقٍّ:** عرض الشاشات على شاشة سطح مكتب عريضة، وفحص قبل/بعد في المتصفح (تم على خدمة SQLite/PG عبر HTTP).

### تطبيق Flutter: الإعلانات والإشعارات والملف الشخصي — ✅ منجز (26 ت10 2026)
- ثلاث شاشات جديدة + شارة غير المقروء + بطاقة الملف الشخصي، مع 22 اختباراً جديداً (65/65) و`analyze` نظيف
  و`build web` و**APK 67.8MB**.
- **متبقٍّ:** تجربة الشاشات على جهاز حقيقي مع إشعارات فعلية (FCM غير مفعّل بعد الإرسال).

### نشر بلا Docker — ✅ ملفات جاهزة (26 ت10 2026)
- `deploy/systemd` + `deploy/nginx` + `deploy/DEPLOY.md` + `api.env.example`، ومسار النسخ الاحتياطي المجدول.
- **غير متحقق:** تحميل الوحدات و`nginx -t` وTLS على سيرفر حقيقي (لا systemd/Nginx على ويندوز).

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

> اقرأ `csit-app/HANDOFF.md` كاملاً، ثم افحص حالة المستودع الفعلية (لا تعتمد على ذاكرة سابقة)، وشغّل اختبارات الـAPI على SQLite وPostgreSQL و`flutter analyze`/`flutter test` لتأكيد الحالة. بعدها ابدأ من «الخطوات التالية» في القسم 7 — **N7 (الاعتماد التجريبي)** — وأبلغني بما تحققت منه وما لم يتحقق.

---

### سجل التغييرات المختصر
- **25 ت10 2026:** المرحلة 1 (29 جدولاً + الأقسام + لوحة أولية) والمرحلة 2 (مصادقة + استيراد + تدقيق) — 27 اختباراً على القاعدتين.
- **26 ت10 2026:** المرحلة 3 (حضور QR + جدول + تعارضات + فهرس جزئي + CI) — **43 اختباراً** على القاعدتين، ونموذج الشاشات الثماني.
- **26 ت10 2026 (تكملة):** N1 — الحضور في Flutter (مسح QR للطالب + قائمة لحظية وQR متجدد للتدريسي) — **27/27** اختبار واجهة، `analyze` نظيف، `build web` ناجح، **أول APK ناجح (66.5MB)**، وإعادة إنشاء `ci.yml` المفقود.
- **26 ت10 2026 (N2):** الجدول والمواد والدرجات في Flutter + `GET /offerings` — **43/43** اختبار واجهة و**65/65** على القاعدتين، وAPK 67.5MB.
- **26 ت10 2026 (GitHub):** رفع المستودع إلى `JJ36t/csit-app` — **CI أخضر 3/3 من أول تشغيل فعلي**.
- **26 ت10 2026 (N4):** شاشات لوحة التحكم الثلاث (طلاب/جدول/درجات) + `GET /admin/timetable/{rooms,slots}` و`slot_id` في `/timetable` — **69/69** على SQLite، `npm run build` ناجح، `smoke_n4` أخضر، وتجربة يدوية بحساب `ADMIN-001`.
- **26 ت10 2026 (N5):** Redis لحدّ المحاولات (برجوع آلي للذاكرة) + نسخ/استرجاع مُجرَّب (94.6KB · 5/0/1 · 0003) + `docker-compose`/Dockerfiles/Nginx + `/health` عميق — **80/80** على القاعدتين.
- **26 ت10 2026 (شاشات اللوحة):** الإعلانات + المستخدمون + سجل التدقيق (ترحيل `0004`) + لوحة الملخص — **93/93** على القاعدتين، بناء اللوحة ناجح، وتجربة يدوية للأربع.
- **26 ت10 2026 (تطبيق/نشر):** شاشات الإعلانات والإشعارات والملف الشخصي في Flutter (65/65 · APK 67.8MB) + حزمة نشر systemd/Nginx بلا Docker.
- **26 ت10 2026 (تحقق بيئي):** Redis حقيقي (5→429→تصفير) + محاولة Docker (مثبّت، محرّك معطّل) + إصلاح ترحيل `0004` على SQLite باختبار انحدار — **94/94** على القاعدتين.
- **26 ت10 2026 (Docker):** WSL2 ثم حزمة compose كاملة (3 خدمات healthy · health 503/200 · بقاء الملفات · نسخ/استرجاع 86.4KB · لوحة على 8080) + سكربتا `compose-smoke` و`backup-compose`.
