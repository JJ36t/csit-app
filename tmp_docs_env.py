# -*- coding: utf-8 -*-
"""توثيق التحقق البيئي: Redis حقيقي، محاولة Docker، وإصلاح ترحيل 0004 على SQLite."""
from pathlib import Path

ROOT = Path(".")

# ------------------------------------------------------------------ HANDOFF.md
p = ROOT / "HANDOFF.md"
text = p.read_text(encoding="utf-8")

reps = [
    (
        "4. الحالة الحالية للاختبارات: **93/93 على SQLite و93/93 على PostgreSQL** (الترحيلات 0001–0004)، "
        "و`alembic check` نظيف، و`smoke_n4` أخضر، ودورة نسخ/استرجاع مُجرَّبة، وFlutter **43/43**.",
        "4. الحالة الحالية للاختبارات: **94/94 على SQLite و94/94 على PostgreSQL** (الترحيلات 0001–0004)، "
        "و`alembic check` نظيف، و`smoke_n4` أخضر، ودورة نسخ/استرجاع مُجرَّبة، و**Redis حقيقي مُختبَر**، "
        "وFlutter **65/65**.",
    ),
    (
        "| اختبارات API على SQLite | `pytest tests -q` | **93/93** |\n"
        "| اختبارات API على PostgreSQL 18.6 | `DATABASE_URL=postgresql+psycopg://…` | **93/93** |",
        "| اختبارات API على SQLite | `pytest tests -q` | **94/94** |\n"
        "| اختبارات API على PostgreSQL 18.6 | `DATABASE_URL=postgresql+psycopg://…` | **94/94** |",
    ),
    (
        "| حزمة Docker | `docker compose up` | **غير متحقق** — Docker غير مثبت؛ فحص YAML/ملفات فقط |",
        "| حزمة Docker | winget + `docker compose config` | **جزئي**: Docker Desktop مثبّت (CLI 29.9.2 · Compose 5.6.1) و`compose config` صالح (3 خدمات)، لكن المحرّك لا يعمل: خدمة `com.docker.service` تتطلب صلاحية مدير وWSL2 غير مثبّت — بناء الصور/`up` غير متحقق |",
    ),
    (
        "| Redis فعلي | خدمة Redis | **غير متحقق** — لا خدمة على الجهاز؛ المسار مغطّى بـfakeredis |",
        "| Redis فعلي (5.0.14.1 محلي) | `scripts/check_redis.py` + هجوم دخول حقيقي | ✅ عدّاد 2 · TTL 60s · حجب · تصفير؛ وخمس محاولات 401 ثم **429** بالعربية مع مفتاح `ratelimit:<رقم>|<ip>` في Redis |\n"
        "| ترحيل 0004 على قاعدة فيها بيانات | SQLite (21 صفاً) + PostgreSQL (صف) | ✅ بعد إصلاح batch: العمود أُضيف، الصفوف حصلت على وقت، الفهارس باقية، و`downgrade` نظيف |",
    ),
]
for old, new in reps:
    assert text.count(old) == 1, old[:60]
    text = text.replace(old, new)

stage_anchor = "\n---\n\n## 3) حالة التحقق"
stage12 = """
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
"""
assert text.count(stage_anchor) == 1
text = text.replace(stage_anchor, stage12 + stage_anchor)

# تحديث حالة N5
old_n5_tail = "- **متبقٍ:** بناء صور Docker وتشغيل compose (Docker غير مثبت هنا) · Redis فعلي (غير مثبت) · TLS/Nginx على\n  سيرفر الجامعة (يحتاج النطاق والشهادة وتفاصيل الوحدة)."
new_n5_tail = "- **متبقٍ:** بناء صور Docker وتشغيل compose (الثنائيات مثبتة لكن المحرّك يحتاج مديراً + WSL2) · TLS/Nginx على\n  سيرفر الجامعة (يحتاج النطاق والشهادة وتفاصيل الوحدة). Redis صار **متحقَّقاً فعلياً** محلياً (5.0.14.1)."
assert text.count(old_n5_tail) == 1
text = text.replace(old_n5_tail, new_n5_tail)

old_trap = "13. **اختبار يعتمد على `DateTime.now()` قد يعبر منتصف الليل** (فشل اختبار الجدول بعد 22:00 بغداد):\n    ثبّت اللحظات على صباح اليوم بتوقيت بغداد (`todayUtc.add(hours: 5)`) بدل `now.add(hours: 2)`."
new_trap = old_trap + "\n14. **SQLite يرفض `ADD COLUMN ... DEFAULT CURRENT_TIMESTAMP`** على جدول فيه صفوف: أي ترحيل يضيف عموداً\n    بـ`server_default=func.now()` يجب أن يستخدم `op.batch_alter_table` على SQLite (انظر `0004`)."
assert text.count(old_trap) == 1
text = text.replace(old_trap, new_trap)

old_log = "- **26 ت10 2026 (تطبيق/نشر):** شاشات الإعلانات والإشعارات والملف الشخصي في Flutter (65/65 · APK 67.8MB) + حزمة نشر systemd/Nginx بلا Docker."
new_log = old_log + "\n- **26 ت10 2026 (تحقق بيئي):** Redis حقيقي (5→429→تصفير) + محاولة Docker (مثبّت، محرّك معطّل) + إصلاح ترحيل `0004` على SQLite باختبار انحدار — **94/94** على القاعدتين."
assert text.count(old_log) == 1
text = text.replace(old_log, new_log)
p.write_text(text, encoding="utf-8")

# --------------------------------------------------------------- START-HERE.md
p = ROOT / "START-HERE.md"
text = p.read_text(encoding="utf-8")

start_reps = [
    ("# API على SQLite — يجب 93/93", "# API على SQLite — يجب 94/94"),
    ("# API على PostgreSQL — يجب 93/93 (يحتاج كلمة مرور postgres من صاحب المشروع)", "# API على PostgreSQL — يجب 94/94 (يحتاج كلمة مرور postgres من صاحب المشروع)"),
    (
        "الأرقام الحقيقية الآن: **API 93/93 على SQLite و93/93 على PostgreSQL** (ترحيلات 0001–0004) ·",
        "الأرقام الحقيقية الآن: **API 94/94 على SQLite و94/94 على PostgreSQL** (ترحيلات 0001–0004) ·",
    ),
    (
        "غير متحقق: صور Docker، Redis فعلي، TLS، وعرض الشاشات على سطح مكتب عريض.",
        "**Redis حقيقي مُختبَر** (5→429→تصفير) · Docker Desktop مثبّت لكن محرّكه يحتاج مديراً + WSL2 → بناء الصور غير متحقق ·\nغير متحقق أيضاً: TLS، وعرض شاشات اللوحة على سطح مكتب عريض.",
    ),
    ("# فحص عميق ونسخ احتياطي (يحتاج PostgreSQL + كلمة المرور)\ncd ../api; python scripts/backup_db.py; python scripts/verify_restore.py",
     "# فحص عميق ونسخ احتياطي (يحتاج PostgreSQL + كلمة المرور)\ncd ../api; python scripts/backup_db.py; python scripts/verify_restore.py\n\n# فحص Redis الحقيقي (يحتاج خدمة Redis على 6379)\n$env:REDIS_URL='redis://127.0.0.1:6379/0'; python scripts/check_redis.py"),
]
for old, new in start_reps:
    assert text.count(old) == 1, old[:60]
    text = text.replace(old, new)

old_trap_st = "13. **اختبار يعتمد على `DateTime.now()` قد يعبر منتصف الليل** (فشل اختبار الجدول بعد 22:00 بغداد):\n    ثبّت اللحظات على صباح اليوم بتوقيت بغداد (`todayUtc.add(hours: 5)`) بدل `now.add(hours: 2)`."
new_trap_st = old_trap_st + "\n14. **SQLite لا يقبل `ADD COLUMN` بقيمة افتراضية غير ثابتة** على جدول فيه صفوف — استخدم\n    `op.batch_alter_table` على SQLite (كما في ترحيل `0004`)، وأضف اختبار انحدار على قاعدة فيها بيانات."
assert text.count(old_trap_st) == 1
text = text.replace(old_trap_st, new_trap_st)
p.write_text(text, encoding="utf-8")

# ------------------------------------------------------------------- README.md
p = ROOT / "README.md"
text = p.read_text(encoding="utf-8")

readme_reps = [
    (
        "| api · SQLite | `pytest tests` | ✅ **93/93**",
        "| api · SQLite | `pytest tests` | ✅ **94/94**",
    ),
    (
        "| api · PostgreSQL 18.6 | `pytest tests` | ✅ **93/93** على PostgreSQL أيضاً |",
        "| api · PostgreSQL 18.6 | `pytest tests` | ✅ **94/94** على PostgreSQL أيضاً |",
    ),
    (
        "| api · Redis | `pytest tests/test_rate_limit_redis.py` | ✅ **4/4** بـfakeredis (لا خدمة Redis على الجهاز) |",
        "| api · Redis (حقيقي) | `scripts/check_redis.py` + محاولات دخول | ✅ Redis 5.0.14.1 محلي: عدّاد/TTL/حجب/تصفير، و5 محاولات 401 ثم **429** |\n| api · Redis (وحدات) | `pytest tests/test_rate_limit_redis.py` | ✅ **4/4** بـfakeredis |",
    ),
    (
        "| نشر · Docker | `docker compose up` | ⚠️ **غير متحقق** — Docker غير مثبت على جهاز التطوير |",
        "| نشر · Docker | `docker compose config` | ⚠️ **جزئي** — Docker Desktop مثبّت وملف compose صالح، لكن المحرّك يحتاج مديراً + WSL2 (لا بناء صور) |",
    ),
]
for old, new in readme_reps:
    assert text.count(old) == 1, old[:60]
    text = text.replace(old, new)
p.write_text(text, encoding="utf-8")

# ---------------------------------------------------------------- api/README.md
p = ROOT / "api" / "README.md"
text = p.read_text(encoding="utf-8")

api_reps = [
    (
        "| `scripts/smoke_n4.py` | فحص شاشات اللوحة (طلاب/جدول/درجات) عبر HTTP |",
        "| `scripts/smoke_n4.py` | فحص شاشات اللوحة (طلاب/جدول/درجات) عبر HTTP |\n"
        "| `scripts/check_redis.py` | فحص Redis الحقيقي (عدّاد/TTL/حجب/تصفير) — يتطلب `REDIS_URL` |",
    ),
    (
        "- مغطّى بـ4 اختبارات على مسار Redis عبر `fakeredis` (بلا خدمة خارجية) + اختبارات الذاكرة الحالية.",
        "- مغطّى بـ4 اختبارات على مسار Redis عبر `fakeredis`، ومُتحقَّق فعلياً على Redis 5.0.14.1 محلي:\n"
        "  `$env:REDIS_URL='redis://127.0.0.1:6379/0'; python scripts/check_redis.py`.\n"
        "- للتطوير المحلي على ويندوز: `api/redis-dev.conf` (استماع 127.0.0.1 فقط، بلا حفظ على القرص).",
    ),
]
for old, new in api_reps:
    assert text.count(old) == 1, old[:60]
    text = text.replace(old, new)
p.write_text(text, encoding="utf-8")

print("docs updated: HANDOFF, START-HERE, README, api/README")
