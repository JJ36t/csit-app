# خلفية الخدمة (API) — تطبيق كلية علوم الحاسوب وتكنولوجيا المعلومات

FastAPI + SQLAlchemy 2 + Alembic.

- **الإنتاج (سيرفر الجامعة):** PostgreSQL — `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/csit`
- **التطوير/الاختبار المحلي:** SQLite بلا أي إعداد (`csit_dev.db`)
- **النشر:** `docker compose up -d --build` من جذر المستودع (انظر `docker-compose.yml` و`.env.example`)

## التشغيل السريع

```bash
python -m pip install -r requirements-dev.txt
python -m alembic upgrade head          # 29 جدولاً
python scripts/seed.py                  # الأقسام الأربعة + السنة 2026–2027
python scripts/create_admin.py ADMIN-001 "مدير الكلية" "Admin#2026"
python scripts/demo_seed.py             # بيانات عرض: تدريسي/طالبان/مادة/حصة اليوم
python -m uvicorn app.main:app --reload --port 8000
```

ثم: `http://localhost:8000/docs` (توثيق تفاعلي) أو `/health`.

## الاختبارات والتحقق

```bash
python -m pytest tests -v                                   # على SQLite
DATABASE_URL=postgresql+psycopg://... python -m pytest tests # على PostgreSQL
python -m pytest tests/test_rate_limit_redis.py             # مسار Redis بـfakeredis
```

تغطي: المصادقة (دخول/تجديد بتناوب وكشف إعادة استخدام/خروج/تغيير كلمة مرور)،
ربط الجهاز (جهاز واحد نشط، منع الجهاز الثاني، إعادة الضبط)، نطاق رئيس القسم،
سجل التدقيق، حدّ المحاولات، استيراد Excel (قالب/فحص/أخطاء/إنشاء/تكرار)،
دورة الترحيل كاملة، والقيود الفريدية.

### فحص شامل حقيقي عبر HTTP

```bash
# نافذة أولى
python -m uvicorn app.main:app --port 8123
# نافذة ثانية
python scripts/smoke_e2e.py
```

المسار: دخول مدير ← تنزيل القالب ← استيراد طالب ← دخول الطالب بكلمة المرور الأولية
← رفض جهاز ثانٍ (403) ← إعادة ضبط من المدير ← دخول الجهاز الجديد ← رفض رمز الطالب على نقاط الإدارة.
السكربت قابل للتكرار ويعيد ضبط حالته قبل البدء.

### فحص N3 (الدرجات/المواد/الإعلانات/الإشعارات)

```bash
python scripts/demo_seed.py     # مرة واحدة على قاعدة التطوير
python scripts/smoke_n3.py      # يتطلب خدمة تعمل على 8000
```

يفحص: تقييم ← إدخال درجة ← نشر بموافقة الكلية ← رؤية الطالب للدرجة المنشورة ←
إعلان وإشعار صندوق وارد ← رفع مادة PDF وتنزيلها برابط موقّع.

## حدّ المحاولات عبر Redis

- الافتراضي: عدّاد في الذاكرة (نسخة خدمة واحدة) — مناسب للتطوير.
- عند ضبط `REDIS_URL=redis://host:6379/0` يصبح العدّاد في Redis، وتبقى الواجهة العامة كما هي
  (`guard` / `record` / `clear`) فلا يتغير أي router.
- أي عطل (حزمة غائبة، اتصال، مهلة ثانية واحدة) يُسجَّل تحذيراً واحداً ثم يعمل العدّاد في الذاكرة.
- مغطّى بـ4 اختبارات على مسار Redis عبر `fakeredis` (بلا خدمة خارجية) + اختبارات الذاكرة الحالية.

## النسخ الاحتياطي والاسترجاع

```bash
# نسخة (تقرأ DATABASE_URL وPGPASSWORD من البيئة — لا كلمة مرور في الملفات)
python scripts/backup_db.py
# تحقق: أحدث نسخة (أو --file) إلى قاعدة مؤقتة csit_restore_check ثم مقارنة الأعداد وحذفها
python scripts/verify_restore.py
```

- الملفات في `api/backups/` (مستثناة في `.gitignore`)، والاسم `csit-YYYYMMDD-HHMMSS.dump`.
- الدورة نُفِّذت فعلاً على PostgreSQL 18.6: نسخة 94.6KB ← استرجاع بلا أخطاء ← تطابق
  `users/attendance_records/grades` (5/0/1) ← `0003 (head)` ← حذف القاعدة المؤقتة.
- الإيقاع المقترح: نسخة يومية آلية + تحقق شهري موثّق (انظر `HANDOFF.md` القسم 7 — N5).

## سكربتات التشغيل

| السكربت | الوظيفة |
|---|---|
| `scripts/seed.py` | الأقسام الأربعة + السنة الدراسية الحالية |
| `scripts/create_admin.py` | إنشاء/إعادة تعيين حساب مدير الكلية |
| `scripts/import_students.py` | استيراد طلاب من ملف Excel من سطر الأوامر |
| `scripts/reset_device.py` | إعادة ضبط ربط جهاز مستخدم (بديل CLI عن نقطة الـAPI) |
| `scripts/inspect_db.py` | فحص سريع: عدد الجداول، الأقسام، القيود |
| `scripts/smoke_e2e.py` | الفحص الشامل عبر HTTP |
| `scripts/demo_seed.py` | بيانات عرض قابلة للتكرار (تدريسي/طالبان/مادة/حصة اليوم) |
| `scripts/smoke_n3.py` | فحص دورة الدرجات والمواد والإعلانات عبر HTTP |
| `scripts/dev_reset_devices.py` | تصفير ربط الأجهزة (تطوير فقط) — يحل «هذا الحساب مرتبط بجهاز آخر» |
| `scripts/backup_db.py` | نسخة احتياطية `pg_dump -Fc` إلى `api/backups/` (مستثناة من git) |
| `scripts/verify_restore.py` | استرجاع تحقّقي إلى `csit_restore_check` + مقارنة الأعداد + حذف القاعدة |
| `scripts/smoke_n4.py` | فحص شاشات اللوحة (طلاب/جدول/درجات) عبر HTTP |

## النقاط

| النقطة | الوصف |
|---|---|
| `GET /health` | فحص جهوزية عميق: `status` + `database` + `revision` (503 عند تعطّل القاعدة) |
| `POST /auth/login` | دخول + ربط الجهاز (`device.fingerprint` مطلوب) |
| `POST /auth/refresh` | تجديد (تناوب؛ إعادة استخدام رمز ملغى تُنهي كل الجلسات) |
| `POST /auth/logout` | إنهاء الجلسات |
| `POST /auth/change-password` | تغيير كلمة المرور (يُلغي كل رموز التجديد) |
| `GET /auth/me` | الملف الشخصي (طالب: القسم/المرحلة/الشعبة) |
| `GET /departments` | الأقسام الأربعة |
| `POST /admin/students/import` | استيراد Excel — `dry_run=true` افتراضياً |
| `GET /admin/students/template` | قالب Excel بأعمدة معتمدة |
| `GET /admin/students` | قائمة الطلاب (بحث/قسم/مرحلة/نوع دراسة/ترقيم) |
| `POST /admin/users/{id}/device/reset` | إعادة ضبط ربط الجهاز + إنهاء الجلسات |
| `POST /admin/users/{id}/reset-password` | كلمة مرور مؤقتة تُعرض مرة واحدة |
| `POST /sessions/{id}/open` | فتح جلسة الحضور وإصدار رمز QR (يتجدد كل 20 ثانية) |
| `POST /sessions/{id}/close` | إغلاق الجلسة وتسجيل الغياب لمن لم يحضر |
| `GET /sessions/{id}/live` | القائمة اللحظية والعداد والرمز الحالي |
| `POST /attendance/scan` | مسح الطالب (رمز + جهاز + موقع اختياري) |
| `PATCH /attendance/{id}` | تعديل يدوي مدقَّق (للتدريسي/رئيس القسم) |
| `GET /attendance/summary` | نسب الحضور لكل مادة للطالب |
| `GET /offerings/{id}/attendance` | سجل الطالب في مادة |
| `GET /offerings/{id}/attendance/report` | تقرير المادة لكل الطلاب |
| `GET /timetable?from=&to=` | جدول المستخدم (طالب/تدريسي/رئيس قسم) |
| `GET /timetable/changes` | تغييرات الجدول في نطاق زمني |
| `POST /admin/timetable/rooms` | إنشاء قاعة بإحداثيات ونطاق |
| `POST /admin/timetable/slots` | حصة أسبوعية + توليد جلسات الفصل (بكشف تعارض) |
| `POST /admin/timetable/changes` | إلغاء/نقل/إضافة مؤرخة |
| `POST /assessments` | إنشاء تقييم (بوزن ودرجة عظمى، حدّ الأوزان 100) |
| `POST /assessments/{id}/grades` | إدخال/تعديل دفعي كمسودة — مدقَّق قبل/بعد |
| `POST /assessments/{id}/publish` | نشر بموافقة الكلية (مدير فقط) + إشعار الطلاب |
| `DELETE /assessments/{id}` | حذف ناعم لتقييم غير منشور |
| `GET /offerings/{id}/grades` | مصفوفة الدرجات للتدريسي (طلاب × تقييمات + مجموع موزون) |
| `GET /offerings/{id}/grades/export` | تصدير Excel للمادة |
| `GET /grades` | درجات الطالب — المنشورة فقط |
| `POST /offerings/{id}/materials` | رفع مادة (ملف PDF أو رابط) بتحقق النوع/الحجم |
| `GET /offerings/{id}/materials` | مواد المادة (الطالب يرى المنشور فقط) |
| `DELETE /materials/{id}` | حذف ناعم للمادة |
| `GET /files/{id}/download?expires=&sig=` | تنزيل برابط موقّع قصير العمر (10 دقائق) |
| `POST /admin/announcements` | إعلان بنطاق (كلية/قسم/مرحلة/شعبة/مادة) وجدولة نشر |
| `DELETE /admin/announcements/{id}` | حذف إعلان (بصلاحية نطاقه) |
| `GET /announcements` | خلاصة الإعلانات الموجّهة للمستخدم بعلامة مقروء |
| `POST /announcements/{id}/read` | تعليم إعلان مقروءاً (idempotent) |
| `GET /notifications` | صندوق الإشعارات + عدد غير المقروء |
| `POST /notifications/read-all` · `POST /notifications/{id}/read` | تعليم الكل/واحد مقروءاً |
| `PUT /devices/fcm-token` | تسجيل رمز FCM للجهاز المربوط (الإرسال لاحقاً) |

الأخطاء كلها بالشكل `{code, message_ar, details}` (القسم 9 من الخطة).

## قرارات تصميمية مثبتة (من الخطة، القسم 8)

- كل جدول: `id` (UUID) + `created_at`/`updated_at` (UTC)، والعرض بتوقيت بغداد في التطبيقات.
- حذف ناعم `deleted_at` للكيانات الإدارية؛ السجلات التبادلية (حضور، درجات، تدقيق) append-only.
- قيود فريدة: حضور واحد للطالب في الجلسة، درجة واحدة للطالب في التقييم، تسجيل واحد في المادة، قراءة واحدة للإعلان.
- فهرس `(offering_id, weekday)` لجدول الحصص.
- القوائم (Enums) تُخزَّن **بقيمها النصية الصغيرة** (`student`, `present`, `morning`) لا بأسماء الأعضاء — على PostgreSQL أنواع `ENUM` أصلية.
- «جهاز نشط واحد لكل حساب» يُطبَّق في طبقة الخدمة؛ ويُضاف فهرس فريد جزئي على PostgreSQL عند النشر.

## ملاحظات تنفيذية

- **رموز الحضور:** `token = "<window>.<HMAC-SHA256(secret, session:window)>"`، النافذة = الزمن/20 ثانية، ويُقبل الرمز الحالي والنافذة المجاورة فقط (هرمز قديم 410، تالف 400).
- **ترتيب فحص المسح:** جلسة مفتوحة ← رمز ساري ← طالب مسجَّل ← جهاز مربوط نشط ← لا تسجيل مسبق؛ ثم حاضر/متأخر حسب السماحية، والموقع خارج نطاق القاعة/الحرم يُعلَّم «مشكوكاً» ولا يُرفض.
- **إغلاق الجلسة** يُسجّل غياباً تلقائياً لمن لا سجل له (method=manual)، ومنه تُحسب التقارير والنسب.
- **كشف تعارض الجدول:** قاعة / تدريسي / شعبة — عند إنشاء حصة أو نقلها.
- **أنواع Enum على PostgreSQL:** ترحيل `0001` يُسقط أنواع Enum في `downgrade` (أمر خاص بـPostgreSQL فقط) — بدونه تفشل إعادة الترقية بخطأ «النوع موجود مسبقاً». اختُبرت الدورة كاملة على PostgreSQL 18.6.
- **فهرس «جهاز نشط واحد»** في ترحيل `0002` (فريد جزئي) ومثبت أيضاً في نموذج `Device` حتى لا يظهر انحراف في `alembic check`.
- **حدّ المحاولات** في Redis عند ضبط `REDIS_URL` (نافذة 60 ثانية بـINCR+EXPIRE)، وإلا عدّاد الذاكرة؛ أي عطل في Redis يُسجّل تحذيراً واحداً ويعود للذاكرة بلا إسقاط الطلب.
- **الاستيراد** يُنشئ الشعب الناقصة تلقائياً، ويكتب كل الصفوف في معاملة واحدة، ويُجزِّئ كلمات المرور الأولية بكلفة bcrypt 10 (تُغيَّر إجبارياً عند أول دخول).
- **رئيس القسم** يستورد طلاب قسمه فقط ويُعيد ضبط أجهزتهم فقط (نطاق مفروض في الخدمة).
- **«هذا الحساب مرتبط بجهاز آخر»** = قاعدة الجهاز الواحد: كل متصفح/هاتف بصمة مختلفة. للتطوير: `python scripts/dev_reset_devices.py [رقم جامعي]` ثم الدخول من الجهاز الجديد (لا تستخدمها على الإنتاج؛ هناك تُمرّر عبر إدارة القسم).
- **الدرجات:** الطالب لا يرى إلا التقييمات المنشورة؛ إدخال/تعديل الدرجات مسموح لطاقم المادة فقط وحتى قبل النشر؛ النشر لمدير الكلية وحده ويُشعر المسجَّلين؛ مجموع الأوزان ≤ 100 لكل مادة؛ كل تعديل درجة يُسجَّل في `audit_logs` قبل/بعد.
- **المواد:** تُخزَّن خارج قاعدة البيانات بمفتاح عشوائي في `UPLOAD_DIR` (افتراضي `./uploads`)، بلا استخدام اسم المستخدم في المسار؛ الأنواع المسموحة PDF/صور/فيديو/صوت/Office/نص وحتى 25MB (`MAX_UPLOAD_BYTES`).
- **روابط التنزيل** موقّعة HMAC قصيرة العمر (10 دقائق افتراضياً)؛ الرابط نفسه إذن — لا يكشف مساراً ولا اسماً داخلياً.
- **الإعلانات:** الجمهور يُحلّ من النطاق (كلية/قسم/مرحلة/شعبة/مادة)؛ المجدول يُخفي حتى `publish_at`، وينتهي بـ`expires_at`؛ النشر الفوري يُنشئ صندوق وارد لكل الجمهور.
- **CORS** مفتوح لنطاقات localhost أثناء التطوير (`CORS_ORIGIN_REGEX`) — يبقى مغلقاً في الإنتاج حتى تُضاف أصول الموقع الرسمي.

---

## N8 — V2 والتشغيل (27 ت10 2026)

**ترحيل `0005`:** جدول `push_outbox` + أعمدة `users.totp_*` + `absence_excuses.reviewed_at/review_note`.

| المجموعة | النقاط |
|---|---|
| الأعذار | `POST /excuses` (multipart) · `GET /excuses` · `DELETE /excuses/{id}` · `GET /admin/excuses` · `POST /admin/excuses/{id}/review` |
| الطلبات | `POST /requests` · `GET /requests` · `GET /requests/{id}` · `POST /requests/{id}/messages` · `PATCH /admin/requests/{id}` |
| الهوية | `GET /me/identity-card` · `POST /identity/verify` |
| عام | `GET /public/news` (بلا مصادقة) |
| 2FA | `GET /auth/2fa/status` · `POST /auth/2fa/setup|enable|disable` · `POST /admin/users/{id}/2fa/reset` · حقل `totp_code` في الدخول |
| الإدارة | `GET/POST /admin/groups` · `GET /admin/courses` · `GET/POST /admin/offerings` · `PATCH /materials/{id}` |
| التقارير | `GET /admin/reports/attendance` · `/grades` (`?format=csv` بترميز UTF-8 مع BOM) |
| مزامنة | `updated_since` في `/announcements` · `/notifications` · `/offerings/{id}/materials` + `server_time` |

**الإشعارات:** `services/fcm.py` + `services/push.py` + `services/push_worker.py`.
يُكتب الطابور داخل معاملة الإشعار، ويُفرَّغ كل 15 ثانية (يبدأ من `lifespan` في `app/main.py` عند
`FCM_ENABLED=true`). تشغيل دورة واحدة يدوياً: `python -m app.services.push_worker`.

**سكربتات جديدة:**
```bash
python scripts/demo_full_seed.py --reset   # بيانات عرض كاملة مؤرخة باليوم
python scripts/smoke_demo.py               # 21 فحصاً على حسابات العرض
python scripts/archive_term.py --dry-run   # أرشفة نهاية الفصل (ترقية/تخريج/إغلاق تسجيلات)
```

**حدود معروفة:** الاختبارات الـ128 ناجحة على SQLite وPostgreSQL 18.6.
FCM لم يُرسَل منه إشعار حقيقي بلا حساب خدمة Firebase — يُختبر ببديل محقون في
`tests/test_push.py`.