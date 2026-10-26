# نشر csit-app على سيرفر الجامعة بلا Docker

هذا المسار بديل عن `docker-compose.yml` (الذي يبقى كما هو). المكوّنات على الخادم:

```
Internet ──► Nginx (80/443, TLS) ──► /            → /opt/csit/admin/dist   (SPA)
                                  ├─► /api/       → 127.0.0.1:8000 (uvicorn)
                                  └─► /health     → 127.0.0.1:8000
                                                       │
                                          PostgreSQL محلي (127.0.0.1:5432)
```

خدمة uvicorn واحدة عمداً: عدّاد حدّ المعدل في الذاكرة (عند غياب `REDIS_URL`) لا يُشارَك بين عدة عمليات.

## ملفات هذا المجلد

| الملف | الوجهة على الخادم |
|---|---|
| `systemd/csit-api.service` | `/etc/systemd/system/csit-api.service` |
| `systemd/csit-backup.service` + `.timer` | `/etc/systemd/system/` |
| `systemd/csit-restore-check.service` + `.timer` | `/etc/systemd/system/` |
| `nginx/csit.conf` | `/etc/nginx/sites-available/csit.conf` |
| `api.env.example` | `/etc/csit/api.env` (بعد تعبئة القيم) |

## 0. قبل البدء

- Ubuntu 22.04/24.04 أو Debian 12 (المسارات أدناه تفترضهما؛ انظر ملاحظة RHEL في الخطوة 9).
- سجل DNS من النوع `A` للنطاق يشير إلى عنوان الخادم، والمنفذان 80 و443 مفتوحان.
- Python 3.11+ (صورة Docker تستخدم 3.13)، Node.js 18+ لبناء Vite 5، PostgreSQL 14+.
- صلاحية `sudo` على الخادم.

كل الأوامر تُنفَّذ من طرفية SSH على الخادم.

## 1. حزم النظام

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip postgresql postgresql-client \
                    nginx certbot python3-certbot-nginx git curl ca-certificates
# Node.js 20 (مستودع NodeSource) — Vite 5 يحتاج 18+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node -v && npm -v
```

اضبط المنطقة الزمنية كي تعمل مواعيد المؤقّتات كما تتوقّع:

```bash
sudo timedatectl set-timezone Asia/Baghdad   # أو منطقة الجامعة
timedatectl | grep 'Time zone'
```

## 2. مستخدم النظام `csit` والمجلد `/opt/csit`

```bash
# مستخدم نظام بلا تسجيل دخول، وبيت منفصل عن مجلد النشر (npm يحتاج HOME صالحاً)
sudo useradd --system --create-home --home-dir /var/lib/csit \
             --shell /usr/sbin/nologin csit

sudo mkdir -p /opt/csit
sudo chown csit:csit /opt/csit
```

ضع الشيفرة في `/opt/csit` بإحدى طريقتين:

```bash
# (أ) استنساخ مباشر — /opt/csit فارغ الآن
sudo -u csit git clone <REPO_URL> /opt/csit

# (ب) أو من نسخة محلية/أرشيف: انسخ api/ وadmin/ وdeploy/ فقط
sudo rsync -a --delete --exclude .git --exclude node_modules --exclude venv \
     ./ /opt/csit/
sudo chown -R csit:csit /opt/csit
```

النتيجة المطلوبة: `/opt/csit/api`، `/opt/csit/admin`، `/opt/csit/deploy`.

```bash
sudo -u csit mkdir -p /opt/csit/api/uploads /opt/csit/api/backups
sudo chmod 755 /opt/csit /opt/csit/admin
```

## 3. PostgreSQL: دور وقاعدة

```bash
sudo -u postgres psql -v ON_ERROR_STOP=1 <<'SQL'
CREATE ROLE csit LOGIN PASSWORD 'CHANGE_ME_STRONG_DB_PASSWORD';
CREATE DATABASE csit OWNER csit;
-- لفحص الاسترجاع الشهري: ينشئ ويحذف قاعدة csit_restore_check المؤقتة
ALTER ROLE csit CREATEDB;
SQL
```

- استبدل كلمة المرور، وضع نفسها في `DATABASE_URL` (الخطوة 5).
- اختر كلمة مرور بلا محارف تُكسر داخل رابط URL (`@ : / ? # $ %`) أو %-encode لها.
- `CREATEDB` مطلوب لـ`verify_restore.py` فقط؛ قاعدة المصدر لا تُعدَّل إطلاقاً.

تحقّق أن الاتصال يعمل عبر TCP بكلمة مرور (وليس peer):

```bash
psql "postgresql://csit:CHANGE_ME_STRONG_DB_PASSWORD@127.0.0.1:5432/csit" -c 'select current_database(), current_user'
```

إن فشل، راجع `pg_hba.conf` (يحتاج `host all all 127.0.0.1/32 scram-sha-256`) ثم `sudo systemctl reload postgresql`.

## 4. بيئة Python والاعتماديات

```bash
sudo -u csit -H python3 -m venv /opt/csit/api/venv
sudo -u csit -H /opt/csit/api/venv/bin/pip install --upgrade pip
sudo -u csit -H /opt/csit/api/venv/bin/pip install -r /opt/csit/api/requirements.txt
/opt/csit/api/venv/bin/python -c 'import fastapi, uvicorn, psycopg, alembic; print("deps ok")'
```

## 5. ملف البيئة `/etc/csit/api.env`

```bash
sudo install -d -m 750 /etc/csit
sudo install -m 600 -o root -g root /opt/csit/deploy/api.env.example /etc/csit/api.env
sudo nano /etc/csit/api.env
```

عبّئ على الأقل:

- `DATABASE_URL` بنفس كلمة مرور الخطوة 3.
- `JWT_SECRET` بقيمة مولّدة:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

- `UPLOAD_DIR=/opt/csit/api/uploads` (المجلد أُنشئ في الخطوة 2).

الملف يبقى `600` ومالكه `root`: systemd (PID 1) يقرأه ويمرّر المتغيّرات للخدمة، فلا يحتاج `csit` قراءته. لا تضع أسراراً في ملفات الوحدات أو في المستودع.

## 6. ترحيل المخطط (`alembic upgrade head`)

Alembic يقرأ `DATABASE_URL` من البيئة، والملف أعلاه `600` فلا يقرأه `csit`. شغّل الترحيل كوحدة عابرة يقرأ لها systemd الملف ويهبط إلى المستخدم `csit`:

```bash
sudo systemd-run --pipe --collect --uid=csit --gid=csit \
  --property=WorkingDirectory=/opt/csit/api \
  --property=EnvironmentFile=/etc/csit/api.env \
  /opt/csit/api/venv/bin/alembic upgrade head

# التحقق: يجب أن يطبع رقم الرأس (head)
sudo systemd-run --pipe --collect --uid=csit --gid=csit \
  --property=WorkingDirectory=/opt/csit/api \
  --property=EnvironmentFile=/etc/csit/api.env \
  /opt/csit/api/venv/bin/alembic current
```

أعد الأمر نفسه بعد كل تحديث يضيف migration. (بديل مكافئ: تشغيله داخل جلسة `csit` بعد منحه قراءة مؤقتة للملف، ثم إعادة `chown root:root && chmod 600`.)

## 7. بناء لوحة التحكم

`admin/dist` مستثنى في `.gitignore`، لذا يُبنى على الخادم بعد كل تحديث:

```bash
sudo -u csit -H bash -lc 'cd /opt/csit/admin && npm ci && npm run build'
ls -l /opt/csit/admin/dist/index.html
# nginx (www-data) يحتاج قراءة الملفات وعبور المجلدات
sudo chmod -R a+rX /opt/csit/admin/dist
```

## 8. تفعيل خدمة API

```bash
sudo cp /opt/csit/deploy/systemd/csit-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now csit-api
sudo systemctl status csit-api --no-pager
curl -fsS http://127.0.0.1:8000/health; echo
```

المتوقّع: `{"status":"ok","database":"ok","revision":"<head>"}`. إن ظهر `degraded` فالمشكلة في `DATABASE_URL`/PostgreSQL لا في systemd:

```bash
sudo journalctl -u csit-api -n 50 --no-pager
```

## 9. Nginx

```bash
sudo cp /opt/csit/deploy/nginx/csit.conf /etc/nginx/sites-available/csit.conf
sudo ln -sf /etc/nginx/sites-available/csit.conf /etc/nginx/sites-enabled/csit.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nano /etc/nginx/sites-available/csit.conf   # استبدل csit.example.edu.iq بالنطاق الحقيقي
sudo nginx -t && sudo systemctl reload nginx
```

افتح الجدار الناري (إن كان `ufw` مفعّلاً):

```bash
sudo ufw allow 'Nginx Full'
sudo ufw status
```

المنفذ 8000 مربوط بـ`127.0.0.1` في وحدة systemd، فلا حاجة لفتحه ولا لتحويله.

> على RHEL/Rocky: ضع الملف في `/etc/nginx/conf.d/csit.conf` بلا `sites-enabled`، وافتح 80/443 بـ`firewall-cmd`، وفعّل `sudo setsebool -P httpd_can_network_connect 1` كي يستطيع Nginx الوصول إلى 127.0.0.1:8000.

## 10. شهادة TLS بـcertbot

بعد التأكد أن النطاق يشير إلى الخادم وأن `http://<domain>/` يفتح:

```bash
sudo certbot --nginx -d csit.example.edu.iq --redirect --agree-tos -m admin@example.edu.iq
sudo nginx -t && sudo systemctl reload nginx
sudo certbot renew --dry-run
```

certbot يعدّل `sites-available/csit.conf` في مكانه (يضيف `listen 443 ssl` والتحويل من 80). بعد نجاح TLS فعّل HSTS من الملف إن رغبت، ثم `sudo systemctl reload nginx`. التجديد تلقائي عبر `certbot.timer`؛ تحقّق بـ`systemctl list-timers | grep certbot`.

## 11. فحص نهائي

```bash
curl -fsS https://csit.example.edu.iq/health; echo                 # 200 + status ok
curl -s -o /dev/null -w '%{http_code}\n' https://csit.example.edu.iq/        # 200 (index.html)
curl -s -o /dev/null -w '%{http_code}\n' https://csit.example.edu.iq/admin/users  # 200 (SPA fallback)
curl -sI https://csit.example.edu.iq/ | grep -Ei 'x-content-type|x-frame|referrer'  # الترويسات
curl -s -o /dev/null -w '%{http_code}\n' http://csit.example.edu.iq/        # 301 → https
```

ثم من المتصفح: افتح اللوحة، سجّل الدخول، وارفع ملفاً صغيراً للتأكد من مسار الرفع (`UPLOAD_DIR`).

## 12. النسخ الاحتياطي وفحص الاسترجاع

```bash
sudo cp /opt/csit/deploy/systemd/csit-backup.service /etc/systemd/system/
sudo cp /opt/csit/deploy/systemd/csit-backup.timer /etc/systemd/system/
sudo cp /opt/csit/deploy/systemd/csit-restore-check.service /etc/systemd/system/
sudo cp /opt/csit/deploy/systemd/csit-restore-check.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now csit-backup.timer csit-restore-check.timer
systemctl list-timers 'csit-*'
```

- النسخة اليومية 02:30، والفحص الشهري أول كل شهر 03:30 (بتوقيت الخادم)، وكلاهما `Persistent=true` ليُنفَّذا بعد انقطاع/إطفاء.

تشغيل يدوي أول مرة (لا تنتظر الموعد):

```bash
sudo systemctl start csit-backup.service
sudo journalctl -u csit-backup -n 30 --no-pager
ls -lh /opt/csit/api/backups/

sudo systemctl start csit-restore-check.service
sudo journalctl -u csit-restore-check -n 40 --no-pager
```

المتوقّع في الثاني: أسطر المقارنة `✓ users … ✓ attendance_records … ✓ grades …` ثم
`فحص الاسترجاع نجح: الأعداد مطابقة والنسخة قابلة للاسترجاع.`
إن فشل بصلاحيات إنشاء القاعدة فراجع `ALTER ROLE csit CREATEDB` في الخطوة 3.

## 13. استرجاع فعلي عند كارثة

الفحص الشهري يثبت قابلية الاسترجاع لكنه لا يستبدل تمريناً فعلياً مرة في الفصل.
إن تلفت القاعدة:

```bash
sudo systemctl stop csit-api
sudo -u postgres dropdb --if-exists csit
sudo -u postgres createdb -O csit csit
# pg_restore كمستخدم csit لأنه المالك ولملف النسخة (صلاحية 600)؛ سيطلب كلمة المرور
sudo -u csit /usr/bin/pg_restore --no-owner --no-privileges -h 127.0.0.1 -U csit \
     -d csit /opt/csit/api/backups/csit-YYYYMMDD-HHMMSS.dump
sudo systemctl start csit-api
curl -fsS http://127.0.0.1:8000/health; echo
```

ثم `systemctl start csit-restore-check.service` للتأكد أن الأعداد سليمة، وأعد بناء `dist` إن كانت النسخة أقدم من آخر نشر.

## 14. صيانة

- **النسخ على نفس القرص**: `api/backups` محلي؛ انسخه دورياً خارج الخادم (مثلاً `rsync` إلى تخزين الجامعة) وإلا فكارثة القرص تُفقد الاثنين.
- **لا تقليم تلقائي**: `backup_db.py` لا يحذف القديم. راقب المساحة، أو أضف مهمة مثل:
  `sudo -u csit find /opt/csit/api/backups -name 'csit-*.dump' -mtime +90 -delete`
- **بعد كل تحديث**: `git pull` → `pip install -r requirements.txt` → `alembic upgrade head` (الخطوة 6) → `npm ci && npm run build` (الخطوة 7) → `systemctl restart csit-api`.
- **السجلات**: `journalctl -u csit-api -f`؛ لا ملفات سجل على القرص (stdout فقط).

## استكشاف الأخطاء

| العرض | السبب المرجّح | العلاج |
|---|---|---|
| 502 Bad Gateway | `csit-api` متوقف أو على منفذ آخر | `systemctl status csit-api`، `ss -ltnp \| grep 8000` |
| 404 عند تحديث صفحة داخل اللوحة | غياب SPA fallback | تأكد من `try_files $uri $uri/ /index.html` ثم `nginx -t` |
| 413 على رفع ملف | حجم أكبر من `client_max_body_size` | القيمة 30m تغطي 25MB + هامش multipart؛ راجع حجم الملف |
| `/health` يعيد 503 | قاعدة البيانات غير متاحة أو الترحيل ناقص | `DATABASE_URL`، حالة PostgreSQL، `alembic current` |
| `permission denied` على `dist` | `www-data` لا يعبر المجلدات | `chmod -R a+rX /opt/csit/admin/dist` |
| فشل مصادقة PostgreSQL | محارف خاصة في كلمة المرور أو `pg_hba` | %-encode للمحارف، أو `scram-sha-256` لـ127.0.0.1 |
| فشل الفحص الشهري بصلاحية إنشاء قاعدة | الدور بلا `CREATEDB` | `ALTER ROLE csit CREATEDB` |

## خارج نطاق هذا الملف

مراقبة TLS والتجديد من خارج الخادم (Uptime Kuma يقيس `/health`)، تدوير سجلات journald، نسخ احتياطي خارج الموقع، وأي إعداد جدار ناري على مستوى الشبكة الجامعية — كلها قرارات تشغيل يحددها فريق السيرفر.
