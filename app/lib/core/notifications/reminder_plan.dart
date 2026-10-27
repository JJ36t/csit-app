import '../../features/timetable/data/timetable_api.dart';
import '../utils/date_utils.dart';

/// تذكير مجدول واحد — بيانات خالصة قابلة للاختبار بلا أي إضافة من Flutter.
class ScheduledReminder {
  const ScheduledReminder({
    required this.id,
    required this.at,
    required this.title,
    required this.body,
  });

  final int id;
  final DateTime at;
  final String title;
  final String body;
}

class ReminderPlan {
  const ReminderPlan({required this.reminders});

  final List<ScheduledReminder> reminders;

  bool get isEmpty => reminders.isEmpty;
}

/// يبني خطة التذكيرات من جدول الطالب:
/// - تذكير قبل كل محاضرة بـ15 دقيقة (خلال 7 أيام قادمة).
/// - ملخص لمحاضرات الغد عند الساعة 20:00 (أو 20:00 من الغد إن تجاوزناها).
///
/// لا نجدول تذكيراً لوقت مضى (أقل من دقيقة)، ولا نكرر المعرّفات كي
/// يستبدل `cancelAll` القديم بلا تراكم إشعارات.
ReminderPlan buildReminderPlan({
  required List<SessionItem> sessions,
  required DateTime now,
  required String Function(SessionItem session) lectureTitle,
  required String Function(SessionItem session) lectureBody,
  required String digestTitle,
  required String Function(int count, String time) digestBody,
  Duration lead = const Duration(minutes: 15),
  int digestHour = 20,
  int horizonDays = 7,
}) {
  final localNow = now.toLocal();
  final horizon = localNow.add(Duration(days: horizonDays));
  final earliest = localNow.add(const Duration(minutes: 1));
  final reminders = <ScheduledReminder>[];
  var id = 1000;

  for (final session in sessions) {
    final start = session.startsAt.toLocal();
    final fireAt = start.subtract(lead);
    if (!start.isBefore(horizon) || !fireAt.isAfter(earliest)) {
      continue;
    }
    reminders.add(
      ScheduledReminder(
        id: id++,
        at: fireAt,
        title: lectureTitle(session),
        body: lectureBody(session),
      ),
    );
  }

  // ملخص الغد
  var digestAt = DateTime(localNow.year, localNow.month, localNow.day, digestHour);
  if (!digestAt.isAfter(localNow)) {
    digestAt = digestAt.add(const Duration(days: 1));
  }
  final targetDay = DateTime(digestAt.year, digestAt.month, digestAt.day)
      .add(const Duration(days: 1));
  final tomorrow = sessions.where((session) {
    final local = toBaghdad(session.startsAt);
    return local.year == targetDay.year &&
        local.month == targetDay.month &&
        local.day == targetDay.day;
  }).toList()
    ..sort((a, b) => a.startsAt.compareTo(b.startsAt));

  if (tomorrow.isNotEmpty) {
    reminders.add(
      ScheduledReminder(
        id: 9000,
        at: digestAt,
        title: digestTitle,
        body: digestBody(tomorrow.length, formatHm(tomorrow.first.startsAt)),
      ),
    );
  }

  reminders.sort((a, b) => a.at.compareTo(b.at));
  return ReminderPlan(reminders: reminders);
}
