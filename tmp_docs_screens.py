# -*- coding: utf-8 -*-
"""تحديث الوثائق بعد إنجاز شاشات اللوحة المتبقية (إعلانات/مستخدمون/تدقيق/ملخص)."""
from pathlib import Path

ROOT = Path(".")

# ------------------------------------------------------------------ HANDOFF.md
p = ROOT / "HANDOFF.md"
text = p.read_text(encoding="utf-8")

reps = [
    (
        "4. الحالة الحالية للاختبارات: **80/80 على SQLite و80/80 على PostgreSQL** (الترحيلات 0001–0003)، "
        "و`alembic check` نظيف، و`smoke_n4` أخضر، ودورة نسخ/استرجاع مُجرَّبة، وFlutter **43/43**.",
        "4. الحالة الحالية للاختبارات: **93/93 على SQLite و93/93 على PostgreSQL** (الترحيلات 0001–0004)، "
        "و`alembic check` نظيف، و`smoke_n4` أخضر، ودورة نسخ/استرجاع مُجرَّبة، وFlutter **43/43**.",
    ),
    (
        "6. **التالي فوراً:** بقية شاشات اللوحة (الإعلانات/المستخدمون/سجل التدقيق/لوحة الملخص)، ثم N7 الاعتماد التجريبي. "
        "N5 مكتمل عدا بناء صور Docker (Docker غير مثبت على جهاز التطوير) وشهادة HTTPS (تنتظر تفاصيل سيرفر الجامعة).",
        "6. **التالي فوراً:** N7 — الاعتماد التجريبي (شعبة واحدة لأسبوعين، 20 مختبِراً في Play المغلقة). "
        "لوحة التحكم اكتملت بشاشاتها السبع. متبقٍّ من النشر: بناء صور Docker (Docker غير مثبت) وشهادة HTTPS (تنتظر سيرفر الجامعة).",
    ),
    (
        "| اختبارات API على SQLite | `pytest tests -q` | **80/80** |\n"
        "| اختبارات API على PostgreSQL 18.6 | `DATABASE_URL=postgresql+psycopg://…` | **80/80** |",
        "| اختبارات API على SQLite | `pytest tests -q` | **93/93** |\n"
        "| اختبارات API على PostgreSQL 18.6 | `DATABASE_URL=postgresql+psycopg://…` | **93/93** |",
    ),
    (
        "| الترحيلات على PostgreSQL | `alembic upgrade head` + `alembic check` | 0001+0002+0003 · «No new upgrade operations detected» |",
        "| الترحيلات على PostgreSQL | `alembic upgrade head` + `alembic check` | 0001–0004 · «No new upgrade operations detected» |",
    ),
    (
        "| حزمة Docker | `docker compose up` | **غير متحقق** — Docker غير مثبت؛ فحص YAML/ملفات فقط |",
        "| تجربة يدوية للشاشات الأربع الجديدة | `ADMIN-001` على خدمة حيّة | لوحة الملخص (3 طلاب/جلسة/تقييمان) · إعلان يُنشأ ثم يُحذف · قائمة 5 مستخدمين + كلمة مرور مؤقتة تُعرض مرة · سجل تدقيق بأوقات بغداد وترشيح `password_reset` = سجل واحد |\n"
        "| حزمة Docker | `docker compose up` | **غير متحقق** — Docker غير مثبت؛ فحص YAML/ملفات فقط |",
    ),
]
for old, new in reps:
    assert text.count(old) == 1, old[:60]
    text = text.replace(old, new)

# شجرة الملفات
tree_reps = [
    (
        "│   ├── routers/           ← auth, admin_users, admin_students, admin_timetable, attendance, timetable,\n"
        "│   │                        departments, health, grades, materials, announcements, notifications, offerings",
        "│   ├── routers/           ← auth, admin_users, admin_students, admin_timetable, admin_audit, admin_overview,\n"
        "│   │                        attendance, timetable, departments, health, grades, materials, announcements,\n"
        "│   │                        notifications, offerings",
    ),
    (
        "│   ├── migrations/versions/   ← 0001_initial_schema · 0002_device_unique_active · 0003_materials_announcements",
        "│   ├── migrations/versions/   ← 0001_initial_schema · 0002_device_unique_active · 0003_materials_announcements ·\n"
        "│   │                            0004_audit_created_at",
    ),
]
for old, new in tree_reps:
    assert text.count(old) == 1, old[:60]
    text = text.replace(old, new)

old_admin_tree = "│   └── src/  ← App.tsx, api.ts, pages/{LoginPage, StudentsPage, TimetablePage, GradesPage}"
assert text.count(old_admin_tree) == 1
text = text.replace(
    old_admin_tree,
    "│   └── src/  ← App.tsx, api.ts, pages/{LoginPage, StudentsPage, TimetablePage, GradesPage,\n"
    "│                          AnnouncementsPage, UsersPage, AuditPage, DashboardPage}",
)

# قسم 2: المرحلة 9
stage_anchor = "\n---\n\n## 3) حالة التحقق"
stage9 = """
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
"""
assert text.count(stage_anchor) == 1
text = text.replace(stage_anchor, stage9 + stage_anchor)

# قسم 7: الشاشات المتبقية
n6_anchor = "### N6 — Git وCI"
screens = """### بقية شاشات اللوحة (الإعلانات/المستخدمون/الترشيح/الملخص) — ✅ منجز (26 ت10 2026)
- الإعلانات (قائمة إدارية بالحالة + إنشاء/حذف) · المستخدمون (قائمة + إعادة ضبط جهاز/كلمة مرور) ·
  سجل التدقيق (ترحيل 0004 + ترشيح + قبل/بعد) · لوحة الملخص (أرقام حقيقية بنطاق القسم).
- **قبول متحقق:** 93/93 على القاعدتين · بناء اللوحة ناجح · تجربة يدوية للأربعة · لا أسرار في الاستجابات.
- **ملاحظة نطاق:** سجل التدقيق لمدير الكلية فقط؛ رئيس القسم يحصل على 403 عربية.
- **متبقٍّ:** عرض الشاشات على شاشة سطح مكتب عريضة، وفحص قبل/بعد على PostgreSQL في المتصفح (تم على SQLite/HTTP).

"""
assert text.count(n6_anchor) == 1
text = text.replace(n6_anchor, screens + n6_anchor)

# برومبت الحساب الجديد
old_prompt = "بعدها ابدأ من «الخطوات التالية» في القسم 7 — **بقية شاشات اللوحة (الإعلانات/المستخدمون/سجل التدقيق/لوحة الملخص)** — وأبلغني بما تحققت منه وما لم يتحقق."
new_prompt = "بعدها ابدأ من «الخطوات التالية» في القسم 7 — **N7 (الاعتماد التجريبي)** — وأبلغني بما تحققت منه وما لم يتحقق."
assert text.count(old_prompt) == 1
text = text.replace(old_prompt, new_prompt)

# سجل التغييرات
old_log = "- **26 ت10 2026 (N5):** Redis لحدّ المحاولات (برجوع آلي للذاكرة) + نسخ/استرجاع مُجرَّب (94.6KB · 5/0/1 · 0003) + `docker-compose`/Dockerfiles/Nginx + `/health` عميق — **80/80** على القاعدتين."
new_log = old_log + "\n- **26 ت10 2026 (شاشات اللوحة):** الإعلانات + المستخدمون + سجل التدقيق (ترحيل `0004`) + لوحة الملخص — **93/93** على القاعدتين، بناء اللوحة ناجح، وتجربة يدوية للأربع."
assert text.count(old_log) == 1
text = text.replace(old_log, new_log)
p.write_text(text, encoding="utf-8")

# --------------------------------------------------------------- START-HERE.md
p = ROOT / "START-HERE.md"
text = p.read_text(encoding="utf-8")

start_reps = [
    (
        "**التالي:** بقية شاشات اللوحة (الإعلانات/المستخدمون/سجل التدقيق/لوحة الملخص)، ثم N7 الاعتماد التجريبي.\n"
        "N5 منجز عدا ما يحتاج بيئة غير متوفرة: بناء صور Docker (Docker غير مثبت) وشهادة HTTPS (تنتظر سيرفر الجامعة).",
        "**التالي:** N7 — الاعتماد التجريبي (شعبة واحدة لأسبوعين و20 مختبِراً في Play المغلقة).\n"
        "لوحة التحكم اكتملت (سبع شاشات). متبقٍّ من النشر: صور Docker (Docker غير مثبت) وTLS (يحتاج سيرفر الجامعة).",
    ),
    (
        "الأرقام الحقيقية الآن: **API 80/80 على SQLite و80/80 على PostgreSQL** · **Flutter 43/43** و`analyze` نظيف ·\n"
        "**لوحة التحكم**: بناء ناجح وشاشات الطلاب/الجدول/الدرجات مُجرَّبة يدوياً · **نسخ/استرجاع مُجرَّب** (5/0/1 · 0003) ·\n"
        "`/health` عميق (200 · revision 0003) · `alembic` نظيف · **CI أخضر 3/3**. غير متحقق: صور Docker، Redis فعلي، TLS.",
        "الأرقام الحقيقية الآن: **API 93/93 على SQLite و93/93 على PostgreSQL** (ترحيلات 0001–0004) ·\n"
        "**Flutter 43/43** · **لوحة التحكم**: سبع شاشات، بناء ناجح، والأربع الجديدة مُجرَّبة يدوياً ·\n"
        "**نسخ/استرجاع مُجرَّب** · `/health` عميق (revision 0004) · `alembic` نظيف · **CI أخضر 3/3**.\n"
        "غير متحقق: صور Docker، Redis فعلي، TLS، وشاشة سطح مكتب عريضة.",
    ),
    ("# API على SQLite — يجب 80/80", "# API على SQLite — يجب 93/93"),
    ("# API على PostgreSQL — يجب 80/80 (يحتاج كلمة مرور postgres من صاحب المشروع)", "# API على PostgreSQL — يجب 93/93 (يحتاج كلمة مرور postgres من صاحب المشروع)"),
    (
        "admin/src/   App.tsx, api.ts, pages/{LoginPage, StudentsPage, TimetablePage, GradesPage}",
        "admin/src/   App.tsx, api.ts, pages/{LoginPage, StudentsPage, TimetablePage, GradesPage,\n"
        "                                    AnnouncementsPage, UsersPage, AuditPage, DashboardPage}",
    ),
]
for old, new in start_reps:
    assert text.count(old) == 1, old[:60]
    text = text.replace(old, new)

start = text.index("## 6) أين تكمل بالضبط")
end = text.index("## 7) الفخاخ")
new_section = """## 6) أين تكمل بالضبط — **N7: الاعتماد التجريبي**

الهدف: تشغيل حقيقي محدود يجمع ملاحظات قبل التوسع (المرحلة 6 من الخطة).

1. **شعبة واحدة لأسبوعين:** تدريسي واحد + مادة واحدة + 10–20 طالباً حقيقياً (بعد موافقة كتابية على البيانات).
2. **الدرجات:** تقييم واحد يُدخل ويُنشر فعلياً، ومطابقة ما يراه الطالب في التطبيق بما في اللوحة.
3. **الحضور:** فتح جلسة من التطبيق، مسح من هاتف حقيقي (الكاميرا لم تُجرَّب بعد — أهم بند متبقٍ)، وتقارير.
4. **Play المغلقة:** 20 مختبِراً لمدة 14 يوماً، ثم تقرير أخطاء مصنّف (حرج/مهم/تحسين) وإصلاح الحرج.

**معايير القبول:** تقرير اعتماد موثّق (ما جُرّب، من جرّبه، النتيجة) · صفر أخطاء حرجة مفتوحة ·
تحديث `HANDOFF.md` بما تحقق فعلاً على أجهزة حقيقية.

**بالتوازي (اختياري):** بناء صور Docker على جهاز فيه Docker، ثم TLS أمام Nginx على سيرفر الجامعة.

"""
text = text[:start] + new_section + text[end:]

trap_old = "11. **Redis غير مثبت** محلياً: مسار Redis مغطّى بـ`fakeredis` في الاختبارات، وليس بخدمة حقيقية."
trap_new = trap_old + "\n12. **`audit_logs` بلا طابع زمني قبل ترحيل `0004`:** أي قاعدة قديمة تحتاج `alembic upgrade head` قبل شاشة سجل التدقيق، وإلا فشل الاستعلام على العمود الجديد."
assert text.count(trap_old) == 1
text = text.replace(trap_old, trap_new)
p.write_text(text, encoding="utf-8")

print("docs updated: HANDOFF, START-HERE")
