# -*- coding: utf-8 -*-
"""توثيق تشغيل حزمة Docker والتحقق الشامل منها."""
from pathlib import Path

ROOT = Path(".")

# ------------------------------------------------------------------ HANDOFF.md
p = ROOT / "HANDOFF.md"
text = p.read_text(encoding="utf-8")

reps = [
    (
        "و**Redis حقيقي مُختبَر**، ",
        "و**Redis حقيقي** و**حزمة Docker** مُختبَران، ",
    ),
    (
        "متبقٍّ من النشر: بناء صور Docker (Docker غير مثبت) وشهادة HTTPS (تنتظر سيرفر الجامعة).",
        "متبقٍّ من النشر: شهادة HTTPS فقط (تنتظر سيرفر الجامعة).",
    ),
    (
        "| حزمة Docker | winget + `docker compose config` | **جزئي**: Docker Desktop مثبّت (CLI 29.9.2 · Compose 5.6.1) و`compose config` صالح (3 خدمات)، لكن المحرّك لا يعمل: خدمة `com.docker.service` تتطلب صلاحية مدير وWSL2 غير مثبّت — بناء الصور/`up` غير متحقق |",
        "| حزمة Docker | `docker compose up -d --build` + `deploy/compose-smoke.ps1` | ✅ **3 خدمات healthy** (db/api/admin) · `/health` عبر Nginx: 200 و`revision 0004` · 503 `degraded` عند إيقاف القاعدة · الملفات المرفوعة تبقى بعد `restart` · نسخ/استرجاع 86.4KB بأعداد مطابقة · لوحة التحكم تعمل على 8080 · الصور: api 333MB · admin 75.3MB |",
    ),
    (
        "- **متبقٍ:** بناء صور Docker وتشغيل compose (الثنائيات مثبتة لكن المحرّك يحتاج مديراً + WSL2) · TLS/Nginx على\n  سيرفر الجامعة (يحتاج النطاق والشهادة وتفاصيل الوحدة). Redis صار **متحقَّقاً فعلياً** محلياً (5.0.14.1).",
        "- **متبقٍ:** TLS/Nginx على سيرفر الجامعة (يحتاج النطاق والشهادة وتفاصيل الوحدة فقط).\n  Redis (5.0.14.1) وحزمة Docker (3 خدمات + نسخ/استرجاع) **متحقَّقان فعلياً** محلياً.",
    ),
    (
        "21. **SQLite يرفض `ADD COLUMN ... DEFAULT CURRENT_TIMESTAMP`** على جدول فيه صفوف: أي ترحيل يضيف عموداً بـ`server_default=func.now()` يجب أن يستخدم `op.batch_alter_table` على SQLite (انظر `0004` واختبار الانحدار).",
        "21. **SQLite يرفض `ADD COLUMN ... DEFAULT CURRENT_TIMESTAMP`** على جدول فيه صفوف: أي ترحيل يضيف عموداً بـ`server_default=func.now()` يجب أن يستخدم `op.batch_alter_table` على SQLite (انظر `0004` واختبار الانحدار).\n"
        "22. **`docker` يكتب تقدّم البناء وتنبيهات الإضافات على stderr**: مع `$ErrorActionPreference='Stop'` في PowerShell 5.1 يُعامَل ذلك كخطأ يُنهي السكربت. الحل: `2>&1 | Out-Host` أو `2>$null` مع التحقق من `$LASTEXITCODE`. وسكربتات `.ps1` العربية تحتاج **UTF-8 BOM** وإلا فشل تحليلها في 5.1.",
    ),
]
for old, new in reps:
    assert text.count(old) == 1, old[:60]
    text = text.replace(old, new)

stage_anchor = "\n---\n\n## 3) حالة التحقق"
stage13 = """
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
"""
assert text.count(stage_anchor) == 1
text = text.replace(stage_anchor, stage13 + stage_anchor)

old_log = "- **26 ت10 2026 (تحقق بيئي):** Redis حقيقي (5→429→تصفير) + محاولة Docker (مثبّت، محرّك معطّل) + إصلاح ترحيل `0004` على SQLite باختبار انحدار — **94/94** على القاعدتين."
new_log = old_log + "\n- **26 ت10 2026 (Docker):** WSL2 ثم حزمة compose كاملة (3 خدمات healthy · health 503/200 · بقاء الملفات · نسخ/استرجاع 86.4KB · لوحة على 8080) + سكربتا `compose-smoke` و`backup-compose`."
assert text.count(old_log) == 1
text = text.replace(old_log, new_log)
p.write_text(text, encoding="utf-8")

# --------------------------------------------------------------- START-HERE.md
p = ROOT / "START-HERE.md"
text = p.read_text(encoding="utf-8")
reps = [
    (
        "لوحة التحكم اكتملت (سبع شاشات). متبقٍّ من النشر: صور Docker (Docker غير مثبت) وTLS (يحتاج سيرفر الجامعة).",
        "لوحة التحكم اكتملت (سبع شاشات)، وحزمة Docker تعمل عبر Nginx على 8080. متبقٍّ من النشر: TLS فقط (يحتاج سيرفر الجامعة).",
    ),
    (
        "**Redis حقيقي مُختبَر** (5→429→تصفير) · Docker Desktop مثبّت لكن محرّكه يحتاج مديراً + WSL2 → بناء الصور غير متحقق ·",
        "**Redis حقيقي مُختبَر** (5→429→تصفير) · **حزمة Docker مُختبَرة** (3 خدمات · health 503/200 · نسخ/استرجاع) ·",
    ),
    (
        "غير متحقق: صور Docker، Redis فعلي، TLS، وعرض شاشات اللوحة على سطح مكتب عريض.",
        "غير متحقق: TLS، وعرض شاشات اللوحة على سطح مكتب عريض، وكاميرا التطبيق على هاتف حقيقي.",
    ),
]
for old, new in reps:
    assert text.count(old) == 1, old[:60]
    text = text.replace(old, new)

old_trap = "14. **SQLite لا يقبل `ADD COLUMN` بقيمة افتراضية غير ثابتة** على جدول فيه صفوف — استخدم\n    `op.batch_alter_table` على SQLite (كما في ترحيل `0004`)، وأضف اختبار انحدار على قاعدة فيها بيانات."
new_trap = old_trap + "\n15. **`docker` يكتب التقدّم/التنبيهات على stderr**: مع `ErrorActionPreference='Stop'` يُنهي السكربت في PowerShell 5.1.\n    استخدم `2>&1 | Out-Host`، واكتب سكربتات `.ps1` العربية بـ**UTF-8 BOM**."
assert text.count(old_trap) == 1
text = text.replace(old_trap, new_trap)
p.write_text(text, encoding="utf-8")

# ------------------------------------------------------------------- README.md
p = ROOT / "README.md"
text = p.read_text(encoding="utf-8")
reps = [
    (
        "و`admin/nginx.conf` و`.env.example` — **لم تُبنَ الصور** لعدم وجود Docker على جهاز التطوير (فحص ساكن فقط).",
        "و`admin/nginx.conf` و`.env.example` — ثم **بُنيت الصور وشُغِّلت الحزمة** بعد تثبيت WSL2 (المرحلة 13).",
    ),
    (
        "| نشر · Docker | `docker compose config` | ⚠️ **جزئي** — Docker Desktop مثبّت وملف compose صالح، لكن المحرّك يحتاج مديراً + WSL2 (لا بناء صور) |",
        "| نشر · Docker | `docker compose up -d --build` + `deploy/compose-smoke.ps1` | ✅ **3 خدمات healthy** · `/health` عبر Nginx (revision 0004) · 503 عند إيقاف القاعدة · بقاء الملفات بعد restart · نسخ/استرجاع 86.4KB · لوحة على 8080 |",
    ),
    (
        "2. بناء صور Docker وتجربة `docker compose up` على جهاز/سيرفر فيه Docker، ثم TLS أمام Nginx.",
        "2. TLS أمام Nginx على سيرفر الجامعة (وشهادة النطاق) قبل الاعتماد التجريبي.",
    ),
]
for old, new in reps:
    assert text.count(old) == 1, old[:60]
    text = text.replace(old, new)

stage_marker = "## نقاط الـAPI"
stage13 = """**المرحلة 13 — تشغيل حزمة Docker:** بعد تثبيت WSL2 وإعادة التشغيل بُنيت الصورتان وشُغّلت الخدمات الثلاث
(db/api/admin على 8080) healthy، و`/health` عبر Nginx يعيد revision 0004 و503 عند إيقاف القاعدة، والملفات
المرفوعة تبقى بعد إعادة التشغيل، والنسخ/الاسترجاع عبر [deploy/backup-compose.ps1](deploy/backup-compose.ps1)
(86.4KB بأعداد مطابقة). فحص شامل: [deploy/compose-smoke.ps1](deploy/compose-smoke.ps1).

""" + stage_marker
assert text.count(stage_marker) == 1
text = text.replace(stage_marker, stage13)

run_anchor = "**نموذج الشاشات:** [design/screens.html](design/screens.html) — افتحه في المتصفح."
run_new = run_anchor + "\n**Docker Compose:** `Copy-Item .env.example .env` ← املأ القيم ← `docker compose up -d --build` (اللوحة على 8080)، أو `deploy\\compose-smoke.ps1` للفحص الكامل."
assert text.count(run_anchor) == 1
text = text.replace(run_anchor, run_new)
p.write_text(text, encoding="utf-8")

# ---------------------------------------------------------------- deploy/DEPLOY.md
p = ROOT / "deploy" / "DEPLOY.md"
text = p.read_text(encoding="utf-8")
appendix = """

---

## ملحق: وضع Docker Compose (بديل)

إن كان Docker مسموحاً على الخادم فهذا المسار أسرع، ويستخدم نفس `.env`:

```bash
cp .env.example .env        # املأ POSTGRES_PASSWORD وJWT_SECRET
docker compose up -d --build
docker compose exec api python scripts/seed.py
docker compose exec api python scripts/demo_seed.py
docker compose exec api python scripts/create_admin.py ADMIN-001 "مدير الكلية" "Admin#2026"
curl -s http://127.0.0.1:8080/health
```

- **فحص شامل على ويندوز:** `powershell -ExecutionPolicy Bypass -File deploy\\compose-smoke.ps1`
- **نسخ احتياطي (القاعدة غير معروضة على المضيف):** `deploy\\backup-compose.ps1`
  ينفّذ `pg_dump` داخل حاوية `db` وينسخ الملف إلى `api/backups/`، ومع `-Verify` يسترجع لقاعدة مؤقتة ويقارن الأعداد.
- **ملاحظة:** في الحاوية يجب أن يكون `REDIS_URL` اسم خدمة ضمن شبكة compose (أو اتركه فارغاً لعدّاد الذاكرة).
"""
if "ملحق: وضع Docker Compose" not in text:
    text = text.rstrip() + appendix
    p.write_text(text, encoding="utf-8")

print("docs updated")
