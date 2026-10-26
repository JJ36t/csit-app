<#
.SYNOPSIS
  نسخة احتياطية لقاعدة compose (pg_dump داخل حاوية db) مع فحص استرجاع اختياري.

.DESCRIPTION
  في وضع Docker لا تُعرَّض القاعدة على المضيف، لذلك يُنفَّذ pg_dump داخل الحاوية
  ثم تُنسخ النسخة إلى api/backups/ (مستثناة من git).

  الاستخدام:
      powershell -ExecutionPolicy Bypass -File deploy\backup-compose.ps1
      powershell -ExecutionPolicy Bypass -File deploy\backup-compose.ps1 -Verify
#>
param(
  [switch]$Verify
)

$ErrorActionPreference = 'Continue'  # نتحقق من $LASTEXITCODE صراحةً
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path '.env')) { throw 'لا يوجد .env في جذر المستودع' }

$conf = @{}
Get-Content '.env' | Where-Object { $_ -match '^\s*[A-Za-z_][A-Za-z0-9_]*=' } | ForEach-Object {
  $pair = $_ -split '=', 2
  $conf[$pair[0].Trim()] = $pair[1].Trim()
}
$dbUser = if ($conf['POSTGRES_USER']) { $conf['POSTGRES_USER'] } else { 'csit' }
$dbName = if ($conf['POSTGRES_DB']) { $conf['POSTGRES_DB'] } else { 'csit' }

$docker = 'docker'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  $docker = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
  if (-not (Test-Path $docker)) { throw 'لم أجد docker CLI' }
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$remote = "/tmp/csit-$stamp.dump"
New-Item -ItemType Directory -Force -Path 'api\backups' | Out-Null
$local = "api\backups\csit-$stamp.dump"

& $docker compose exec -T db sh -c "pg_dump -U $dbUser -Fc $dbName --file=$remote" 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) { throw 'فشل pg_dump داخل الحاوية' }

& $docker compose cp "db:$remote" $local 2>&1 | Out-Host
$size = [math]::Round((Get-Item $local).Length / 1KB, 1)
Write-Host "✓ نسخة احتياطية: $local ($size KB)"

if ($Verify) {
  $check = 'csit_restore_check'
  # نُعيد الملف إلى الحاوية (حُذف بعد النقل) ثم نسترجع في قاعدة مؤقتة
  & $docker compose cp $local "db:$remote" 2>&1 | Out-Null
  & $docker compose exec -T db dropdb -U $dbUser --if-exists $check 2>&1 | Out-Null
  & $docker compose exec -T db createdb -U $dbUser $check 2>&1 | Out-Host
  & $docker compose exec -T db pg_restore -U $dbUser -d $check $remote 2>&1 | Out-Host

  $tables = @('users', 'attendance_records', 'grades', 'assessments')
  $failed = $false
  foreach ($table in $tables) {
    $source = (& $docker compose exec -T db psql -U $dbUser -d $dbName -tAc "select count(*) from $table").Trim()
    $copy = (& $docker compose exec -T db psql -U $dbUser -d $check -tAc "select count(*) from $table").Trim()
    if ($source -eq $copy) { Write-Host "  ✓ $table : $source / $copy" }
    else { Write-Host "  ✗ $table : $source / $copy"; $failed = $true }
  }

  & $docker compose exec -T db dropdb -U $dbUser --if-exists $check 2>&1 | Out-Null
  & $docker compose exec -T db rm -f $remote 2>&1 | Out-Null
  if ($failed) { throw 'فحص الاسترجاع: الأعداد غير مطابقة' }
  Write-Host '✓ فحص الاسترجاع نجح (القاعدة المؤقتة حُذفت)'
}
