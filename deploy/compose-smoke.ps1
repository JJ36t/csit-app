<#
.SYNOPSIS
  فحص حزمة Docker كاملة (db + api + admin/Nginx) على هذا الجهاز.

.DESCRIPTION
  يشغّل Docker Desktop إن لم يكن المحرّك جاهزاً، ثم `docker compose up -d --build`،
  ينتظر /health عبر Nginx، يزرع الأقسام وبيانات العرض وحساب المدير داخل الحاوية،
  ثم يسجّل الدخول ويقرأ لوحة الملخص ويعرض صفحة اللوحة.

  الاستخدام (من جذر المستودع):
      powershell -ExecutionPolicy Bypass -File deploy\compose-smoke.ps1

  ملاحظات:
  - يتطلب .env محلياً (انسخه من .env.example) وWSL2 مفعّلاً بعد إعادة التشغيل.
  - لا يطبع كلمة مرور المدير؛ يستخدم القيمة الافتراضية للتطوير فقط.
#>
param(
  [string]$BaseUrl = 'http://127.0.0.1:8080',
  [string]$AdminId = 'ADMIN-001',
  [string]$AdminPassword = 'Admin#2026'
)

$ErrorActionPreference = 'Continue'  # نتحقق من $LASTEXITCODE صراحةً
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path '.env')) {
  throw 'لا يوجد .env — انسخه أولاً: Copy-Item .env.example .env ثم املأ القيم'
}

$docker = 'docker'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  $candidate = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
  if (Test-Path $candidate) { $docker = $candidate } else { throw 'لم أجد docker CLI' }
}

function Wait-Engine {
  param([int]$Attempts = 40)
  for ($i = 0; $i -lt $Attempts; $i++) {
    & $docker info 2>$null 1>$null
    if ($LASTEXITCODE -eq 0) { return $true }
    Start-Sleep -Seconds 3
  }
  return $false
}

if (-not (Wait-Engine -Attempts 5)) {
  Write-Host 'تشغيل Docker Desktop…'
  $exe = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
  if (Test-Path $exe) { Start-Process $exe }
  if (-not (Wait-Engine -Attempts 60)) {
    throw 'محرّك Docker لم يبدأ. تأكد من تفعيل WSL2 وإعادة التشغيل، ثم افتح Docker Desktop.'
  }
}
Write-Host '✓ محرّك Docker جاهز'

& $docker compose up -d --build 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) { throw 'فشل docker compose up --build' }

$health = $null
for ($i = 0; $i -lt 60; $i++) {
  try {
    $health = Invoke-RestMethod "$BaseUrl/health" -TimeoutSec 3
    break
  } catch {
    Start-Sleep -Seconds 3
  }
}
if (-not $health) { throw 'لم يستجب /health عبر Nginx — راجع: docker compose logs api admin' }
Write-Host ('✓ /health: ' + ($health | ConvertTo-Json -Compress))

# بيانات العرض وحساب المدير داخل حاوية api (قاعدة جديدة فارغة)
& $docker compose exec -T api python scripts/seed.py | Out-Host
& $docker compose exec -T api python scripts/demo_seed.py | Out-Host
& $docker compose exec -T api python scripts/create_admin.py $AdminId 'مدير الكلية' $AdminPassword | Out-Host

$payload = @{
  university_id = $AdminId
  password      = $AdminPassword
  device        = @{ fingerprint = 'compose-smoke'; model = 'Docker' }
} | ConvertTo-Json -Depth 5
$bytes = [Text.Encoding]::UTF8.GetBytes($payload)
$login = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/auth/login" `
  -ContentType 'application/json; charset=utf-8' -Body $bytes
Write-Host "✓ تسجيل الدخول: $($login.user.full_name_ar) ($($login.user.role))"

$headers = @{ Authorization = "Bearer $($login.access_token)" }
$overview = Invoke-RestMethod "$BaseUrl/api/v1/admin/overview" -Headers $headers
Write-Host "✓ لوحة الملخص: طلاب $($overview.students.total) · جلسات اليوم $($overview.today.sessions) · تقييمات منشورة $($overview.grades.published)"

$index = Invoke-WebRequest "$BaseUrl/" -UseBasicParsing
Write-Host "✓ صفحة اللوحة: HTTP $($index.StatusCode) · $($index.Content.Length) حرفاً"

Write-Host "`nفحص الحزمة نجح — المنظومة تعمل عبر Nginx على $BaseUrl"
