# دليل التشغيل — تطبيق كلية علوم الحاسوب (جامعة القادسية)

> الجمهور: من سيتسلّم التشغيل بعد التسليم (شخصان على الأقل يعرفان هذه الخطوات).
> كل أمر مكتوب ليُنفَّذ كما هو. لا تُخزَّن الأسرار في git.

## 0) ما الذي يعمل وأين

| المكوّن | المكان | ملاحظة |
|---|---|---|
| API (FastAPI) | 127.0.0.1:8000 خلف Nginx | `deploy/systemd/csit-api.service` |
| PostgreSQL | 127.0.0.1:5432 | قاعدة `csit` |
| لوحة التحكم (React) | `/var/www/csit-admin` على `https://<domain>/admin/` | بناء Vite |
| التطبيق (Flutter) | Play Console (مغلق → عام) | APK/AAB |
| المراقبة | Uptime Kuma على 127.0.0.1:3001 | نفق SSH فقط |

## 1) أول نشر (30–45 دقيقة)

```bash
# 1) النظام
sudo apt update && sudo apt install -y python3.13 python3.13-venv nginx postgresql certbot python3-certbot-nginx

# 2) المستخدم والمجلدات
sudo useradd --system --home /opt/csit --shell /usr/sbin/nologin csit
sudo install -d -o csit -g csit /opt/csit/api /var/lib/csit/uploads /var/backups/csit
sudo install -d -o www-data -g www-data /var/www/csit-admin /var/www/csit

# 3) الكود والاعتماديات
sudo -u csit git clone https://github.com/JJ36t/csit-app.git /opt/csit/src
sudo -u csit python3.13 -m venv /opt/csit/venv
sudo -u csit /opt/csit/venv/bin/pip install -r /opt/csit/src/api/requirements.txt

# 4) الأسرار (لا تُلتزم في git)
sudo install -d -m 750 -o root -g csit /etc/csit
sudo tee /etc/csit/api.env >/dev/null <<'ENV'
DATABASE_URL=postgresql+psycopg://csit:CHANGE_ME@127.0.0.1:5432/csit
JWT_SECRET=CHANGE_ME_64_CHARS
IDENTITY_SECRET=CHANGE_ME_ANOTHER_64_CHARS
REDIS_URL=
UPLOAD_DIR=/var/lib/csit/uploads
CORS_ORIGIN_REGEX=https?://(csit\.qu\.edu\.iq)
FCM_ENABLED=false
ENV
sudo chmod 640 /etc/csit/api.env

# 5) القاعدة والترحيلات
sudo -u postgres createuser csit --pwprompt
sudo -u postgres createdb -O csit csit
cd /opt/csit/src/api && sudo -u csit /opt/csit/venv/bin/python -m alembic upgrade head

# 6) الخدمة وNginx
sudo cp deploy/systemd/csit-api.service deploy/systemd/csit-backup.* deploy/systemd/csit-cleanup.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now csit-api csit-backup.timer csit-cleanup.timer
sudo cp deploy/nginx/csit.conf /etc/nginx/sites-available/csit.conf
sudo ln -s /etc/nginx/sites-available/csit.conf /etc/nginx/sites-enabled/
sudo certbot --nginx -d csit.qu.edu.iq
sudo nginx -t && sudo systemctl reload nginx

# 7) فحص
curl -fsS https://csit.qu.edu.iq/health | python -m json.tool
```

## 2) إشعارات الدفع (FCM)

1. أنشئ مشروع Firebase وأضف تطبيق أندرويد باسم الحزمة `iq.edu.qu.csit`.
2. نزّل `google-services.json` وضعه في `app/android/app/` (لا يُلتزم في git إن كان المستودع عاماً — يُسلَّم مع فريق البناء).
3. Project Settings → Service accounts → Generate new private key.
4. على السيرفر أضف إلى `/etc/csit/api.env`:
   ```
   FCM_ENABLED=true
   FCM_PROJECT_ID=<project_id>
   FCM_CLIENT_EMAIL=<client_email>
   FCM_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   ```
5. `sudo systemctl restart csit-api` ثم تحقق:
   ```
   sudo -u csit /opt/csit/venv/bin/python -m app.services.push_worker
   ```
   (يطبع `{"sent": n, ...}` — صفر مقبول إن لم توجد رسائل معلّقة.)
6. من التطبيق: الإعدادات → إشعارات المحاضرات → تفعيل، ثم افتح جلسة من حساب تدريسي وأرسل إعلاناً.

> **بلا إعداد Firebase**: التطبيق يبنى ويعمل، ويبقى صندوق الإشعارات داخل التطبيق.
> `PushService.initialize` يفشل بهدوء ولا يعطّل أي شاشة.

## 3) المصادقة الثنائية

- التدريسي/الإدارة: الإعدادات → التحقق بخطوتين → بدء الإعداد → أضف السرّ إلى
  Google Authenticator → أدخل الرمز → تفعيل.
- فقدان الهاتف: مدير الكلية من لوحة التحكم → المستخدمون → «إعادة ضبط التحقق»
  (`POST /api/v1/admin/users/{id}/2fa/reset`) ثم يسجّل المستخدم من جديد.
- الدخول بلا رمز يعيد `401 totp_required`، والرمز المستعمل سابقاً يعيد `totp_replayed`.

## 4) النسخ الاحتياطي والاسترجاع (تدريب ربع سنوي)

```bash
# نسخة يدوية + تحقق
sudo -u csit /opt/csit/venv/bin/python /opt/csit/api/scripts/backup_db.py --out-dir /var/backups/csit
sudo -u csit /opt/csit/venv/bin/python /opt/csit/api/scripts/verify_restore.py --backup-dir /var/backups/csit

# استرجاع فعلي (تُوقف الخدمة!)
sudo systemctl stop csit-api
sudo -u postgres pg_restore --clean --if-exists -d csit /var/backups/csit/csit-YYYYMMDD-HHMMSS.dump
sudo systemctl start csit-api
curl -fsS http://127.0.0.1:8000/health
```

- النسخ اليومي 02:30 بتوقيت بغداد (`csit-backup.timer` — يعمل على UTC 23:30).
- الاحتفاظ 30 نسخة؛ الأقدم يُحذف من `backup_db.py` تلقائياً؟
  راجع السكربت — إن لم يكن الحذف تلقائياً فأضف `find /var/backups/csit -name '*.dump' -mtime +30 -delete`.
- **التحقق الناجح شرط**: `verify_restore` يستعيد في قاعدة مؤقتة ويقارن العدّادات.

## 4.1) التنظيف الدوري (أسبوعي)

`csit-cleanup.timer` يعمل الأحد 03:00 بغداد ويُنفّذ:
```bash
sudo -u csit /opt/csit/venv/bin/python /opt/csit/api/scripts/cleanup.py --dry-run  # معاينة
sudo -u csit /opt/csit/venv/bin/python /opt/csit/api/scripts/cleanup.py            # تنفيذ
```
- طابور الدفع المنتهي > 14 يوماً · رموز FCM المهجورة > 90 يوماً · رموز التجديد > 30 يوماً.
- مرفقات الأعذار المراجَعة > سنة (يبقى نص العذر، ويُحذف الملف).
- كل تشغيل يُسجّل في `audit_logs` بإجراء `cleanup_run` وبأعداده — راجعه شهرياً.

## 5) المراقبة والتنبيه

```bash
docker compose -f /opt/csit/src/deploy/monitoring/docker-compose.monitoring.yml up -d
ssh -L 3001:127.0.0.1:3001 csit@csit.qu.edu.iq   # ثم http://127.0.0.1:3001
```
راقب: `/health` (كل 60 ثانية) · قاعدة البيانات · `/api/v1/public/news`.
التنبيهات: بريد رئيس القسم + Telegram. **من يرد على التنبيه؟** يُكتب اسمه في هذا الملف.

## 6) الأخطاء الشائعة وحلولها

| العرض | السبب المرجّح | الحل |
|---|---|---|
| «مرتبط بجهاز آخر» | تغيّر الهاتف/أُعيد تثبيت التطبيق | لوحة التحكم → المستخدمون → إعادة ضبط الجهاز |
| التطبيق لا يتصل | API متوقف أو شهادة منتهية | `systemctl status csit-api` · `curl -I https://...` |
| 401 بعد التحديث | `JWT_SECRET` تغيّر | كل المستخدمين يسجّلون من جديد (مقبول في نافذة صيانة) |
| إشعارات لا تصل | `FCM_ENABLED=false` أو رمز جهاز ميت | راجع `api.env` وسجل `push_outbox` |
| «انتهت صلاحية البطاقة» | ساعة الهاتف غير مضبوطة | اضبط «الوقت التلقائي» في الهاتف |
| 413 عند رفع عذر | الملف > 25MB | صغّر الصورة أو ارفع PDF أصغر |

## 7) تدوير الأسرار (كل 6 أشهر)

1. `JWT_SECRET` جديد → كل الجلسات تُلغى (أعلن نافذة صيانة).
2. `IDENTITY_SECRET` جديد → البطاقات القديمة تُرفض خلال 3 دقائق (بلا أثر).
3. كلمة مرور `csit` في القاعدة → حدّث `DATABASE_URL` وأعد التشغيل.
4. مفتاح خدمة Firebase → أنشئ مفتاحاً جديداً ثم احذف القديم من Google Cloud.

## 8) نهاية الفصل الدراسي

```bash
# معاينة أولاً
sudo -u csit /opt/csit/venv/bin/python /opt/csit/api/scripts/archive_term.py --dry-run
# التنفيذ: ترقية المراحل وتخريج الرابعة وإغلاق التسجيلات
sudo -u csit /opt/csit/venv/bin/python /opt/csit/api/scripts/archive_term.py
```
ثم: أنشئ فصلاً جديداً وشعباً من لوحة التحكم (`POST /admin/groups`)، وأنشئ عروض
المواد (`POST /admin/offerings` — يسجّل الطلبة تلقائياً)، وارفع الجدول.

## 9) النشر على Google Play

1. حساب مطوّر + رسوم لمرة واحدة.
2. سياسة الخصوصية منشورة: `https://csit.qu.edu.iq/privacy`.
3. AAB موقّع بمفتاح إصدار (احفظه في خزنة — فقدانه يعني عدم القدرة على التحديث):
   ```bash
   flutter build appbundle --release --dart-define=API_BASE_URL=https://csit.qu.edu.iq
   ```
4. اختبار مغلق 14 يوماً مع 20 مختبِراً، ثم إنتاج.
5. بيانات التطبيق: «لا يجمع» لا تنطبق — أعلن: الموقع (اختياري)، الصور (مرفوعة
   من المستخدم)، معرّفات الجهاز. راجع استمارة Data safety بدقة.

## 10) من يعرف ماذا

| الدور | المسؤولية |
|---|---|
| مسؤول البيانات | الموافقة المكتوبة، سياسة الاحتفاظ، طلبات أصحاب البيانات |
| مسؤول التشغيل | الخدمة، النسخ، الشهادات، التنبيهات |
| مسؤول المحتوى | الحسابات، الشعب، الجدول، الإعلانات |
| الدعم | إعادة ضبط الأجهزة وكلمات المرور |

اكتب الأسماء والأرقام هنا قبل التسليم:
- مسؤول البيانات: ______________________
- مسؤول التشغيل: ______________________ (بديل: ______________________)
- مسؤول المحتوى: ______________________
