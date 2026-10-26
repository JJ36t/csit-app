/// أدوات التاريخ والوقت.
/// قاعدة الخطة: التخزين والتبادل UTC، والعرض بتوقيت بغداد (UTC+3)،
/// والأسبوع يبدأ من الأحد (0) — انظر جدول timetable_slots.
library;

const baghdadOffset = Duration(hours: 3);

/// أسماء الأيام بنفس ترتيب weekday في الخادم (0=الأحد … 6=السبت).
/// تُعرض عبر ملفات l10n وليس من هنا مباشرة في الواجهات.
const weekdayKeys = [
  'sunday',
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
];

/// يحوّل لحظة زمنية إلى توقيت بغداد (UTC+3 ثابتة بلا توقيت صيفي).
DateTime toBaghdad(DateTime moment) => moment.toUtc().add(baghdadOffset);

/// الوقت بالصيغة HH:mm بتوقيت بغداد (لقطة UTC من الخادم أو من الساعة).
String formatHm(DateTime moment) {
  final local = toBaghdad(moment);
  final hh = local.hour.toString().padLeft(2, '0');
  final mm = local.minute.toString().padLeft(2, '0');
  return '$hh:$mm';
}

/// هل تقع اللحظتان في اليوم نفسه بتوقيت بغداد؟
bool isSameBaghdadDay(DateTime a, DateTime b) {
  final first = toBaghdad(a);
  final other = toBaghdad(b);
  return first.year == other.year &&
      first.month == other.month &&
      first.day == other.day;
}

/// التاريخ والوقت بتوقيت بغداد بصيغة YYYY/MM/DD HH:mm — لطوابع الإعلانات والإشعارات.
String formatYmdHm(DateTime moment) {
  final local = toBaghdad(moment);
  final year = local.year.toString().padLeft(4, '0');
  final month = local.month.toString().padLeft(2, '0');
  final day = local.day.toString().padLeft(2, '0');
  return '$year/$month/$day ${formatHm(moment)}';
}
