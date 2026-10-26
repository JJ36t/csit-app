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
| **الإعلانات** (`pages/AnnouncementsPage.tsx`) | إنشاء إعلان بنطاق (كلية/قسم/مرحلة/مادة) وجدولة نشر/انتهاء، وقائمة إدارية بالحالة (نشط/مجدول/منتهٍ) وحذف | `GET /admin/announcements` · `POST /admin/announcements` · `DELETE /admin/announcements/{id}` |
| **المستخدمون** (`pages/UsersPage.tsx`) | قائمة بالبحث والدور والقسم مع حالة الجهاز، وإعادة ضبط الجهاز وكلمة المرور المؤقتة (تُعرض مرة واحدة) | `GET /admin/users` · `POST /admin/users/{id}/device/reset` · `/reset-password` |
| **سجل التدقيق** (`pages/AuditPage.tsx`) | ترشيح بالفاعل/الإجراء/الكيان/المدى الزمني، أوقات بغداد، وصف موسّع يعرض قبل/بعد | `GET /admin/audit` |
| **لوحة الملخص** (`pages/DashboardPage.tsx`) | بطاقات: الطلاب وتوزيعهم، جلسات اليوم وحضورها، التقييمات، الإعلانات | `GET /admin/overview` |
| **الدرجات** (`pages/GradesPage.tsx`) | اختيار المادة، التقييمات وأوزانها (مع منع تجاوز 100)، مصفوفة إدخال دفعي بتمييز الخلايا المعدّلة، حفظ كمسودة، نشر بموافقة مدير الكلية، تصدير Excel | `GET /offerings` · `GET /offerings/{id}/grades` · `POST /assessments` · `POST /assessments/{id}/grades` · `POST /assessments/{id}/publish` · `GET /offerings/{id}/grades/export` |

قواعد ثابتة في الواجهة: النشر مقفول لغير مدير الكلية، وخلايا التقييم المنشور تُقفل (الخادم يرد 409)، وكل رسالة خطأ تُعرض بنص `message_ar` مع رمز الخطأ. وشاشتا الطلاب والجداول تظهران لمدير الكلية/رئيس القسم فقط؛ التدريسي يرى شاشة الدرجات لإدخال المسودات.

## حالة التحقق

- الشاشات السبع مكتملة: الطلاب، الجداول، الدرجات، الإعلانات، المستخدمون، سجل التدقيق، لوحة الملخص.
- تجربة يدوية بحساب `ADMIN-001` على خدمة حيّة للشاشات الأربع الأخيرة (إنشاء/حذف إعلان، كلمة مرور مؤقتة،
  ترشيح سجل التدقيق، أرقام الملخص).

- `npm run build` (tsc + vite) **مُنفَّذ ونجح** بعد N4 (تحذير حجم الحزمة >500KB متوقع — لا يفشل البناء).
- تجربة يدوية حيّة بحساب `ADMIN-001` على الشاشات الثلاث (خدمة `uvicorn` + `vite dev`) — التفاصيل في `HANDOFF.md` القسم 7.
- فحص HTTP مرافق: `python scripts/smoke_n4.py` من مجلد `api/`.
