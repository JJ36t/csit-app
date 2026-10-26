# لوحة التحكم — React + Vite + Ant Design

واجهة الإدارة بواجهة عربية RTL: **الطلاب · الجداول · الدرجات** (منجزة)، والإعلانات/المستخدمون/سجل التدقيق (قيد التنفيذ).

## التشغيل

```bash
npm install
npm run dev      # التطوير على http://localhost:5173 — يوجّه /api إلى 127.0.0.1:8000
npm run build    # بناء إنتاجي في dist/
```

## الشاشات المنجزة (N4)

| الشاشة | ما تفعله | نقاط الـAPI |
|---|---|---|
| **الطلاب** (`pages/StudentsPage.tsx`) | قائمة بترشيح القسم/المرحلة/الدراسة والبحث، واستيراد Excel بخطوتَي فحص ثم تنفيذ مع تقرير أخطاء عربي (صف/عمود/سبب) | `GET /departments` · `GET /admin/students` · `GET /admin/students/template` · `POST /admin/students/import?dry_run=` |
| **الجداول** (`pages/TimetablePage.tsx`) | الحصص في نطاق زمني، التغييرات المؤرخة، الخطة الأسبوعية، وإدارة القاعات والحصص والتغييرات مع عرض رسالة التعارض العربية كما يعيدها الخادم | `GET /timetable` · `GET /timetable/changes` · `GET /admin/timetable/{rooms,slots}` · `POST /admin/timetable/{rooms,slots,changes}` |
| **الدرجات** (`pages/GradesPage.tsx`) | اختيار المادة، التقييمات وأوزانها (مع منع تجاوز 100)، مصفوفة إدخال دفعي بتمييز الخلايا المعدّلة، حفظ كمسودة، نشر بموافقة مدير الكلية، تصدير Excel | `GET /offerings` · `GET /offerings/{id}/grades` · `POST /assessments` · `POST /assessments/{id}/grades` · `POST /assessments/{id}/publish` · `GET /offerings/{id}/grades/export` |

قواعد ثابتة في الواجهة: النشر مقفول لغير مدير الكلية، وخلايا التقييم المنشور تُقفل (الخادم يرد 409)، وكل رسالة خطأ تُعرض بنص `message_ar` مع رمز الخطأ. وشاشتا الطلاب والجداول تظهران لمدير الكلية/رئيس القسم فقط؛ التدريسي يرى شاشة الدرجات لإدخال المسودات.

## حالة التحقق

- `npm run build` (tsc + vite) **مُنفَّذ ونجح** بعد N4 (تحذير حجم الحزمة >500KB متوقع — لا يفشل البناء).
- تجربة يدوية حيّة بحساب `ADMIN-001` على الشاشات الثلاث (خدمة `uvicorn` + `vite dev`) — التفاصيل في `HANDOFF.md` القسم 7.
- فحص HTTP مرافق: `python scripts/smoke_n4.py` من مجلد `api/`.
