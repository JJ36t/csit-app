import 'package:csit/core/notifications/reminder_plan.dart';
import 'package:csit/features/timetable/data/timetable_api.dart';
import 'package:flutter_test/flutter_test.dart';

SessionItem _session({
  required DateTime startsAt,
  String course = 'مقدمة في علوم الحاسوب',
  String room = 'قاعة 101',
}) {
  return SessionItem(
    sessionId: 's-${startsAt.millisecondsSinceEpoch}',
    offeringId: 'o-1',
    date: DateTime(startsAt.year, startsAt.month, startsAt.day),
    startsAt: startsAt.toUtc(),
    endsAt: startsAt.add(const Duration(minutes: 90)).toUtc(),
    courseCode: 'CS101',
    courseNameAr: course,
    kind: 'theory',
    room: room,
    status: 'scheduled',
  );
}

ReminderPlan _plan(List<SessionItem> sessions, DateTime now) => buildReminderPlan(
      sessions: sessions,
      now: now,
      lectureTitle: (_) => 'محاضرة بعد 15 دقيقة',
      lectureBody: (session) => '${session.courseNameAr} — ${session.room}',
      digestTitle: 'محاضرات الغد',
      digestBody: (count, time) => '$count محاضرة تبدأ $time',
    );

void main() {
  final now = DateTime(2026, 10, 27, 9, 0);

  test('تذكير قبل المحاضرة بخمس عشرة دقيقة', () {
    final start = DateTime(2026, 10, 27, 10, 0);
    final plan = _plan([_session(startsAt: start)], now);

    expect(plan.reminders, hasLength(1));
    expect(plan.reminders.first.at, DateTime(2026, 10, 27, 9, 45));
    expect(plan.reminders.first.title, 'محاضرة بعد 15 دقيقة');
    expect(plan.reminders.first.body, contains('قاعة 101'));
  });

  test('لا تذكير لمحاضرة مضت أو تبدأ خلال أقل من دقيقة', () {
    final past = DateTime(2026, 10, 27, 8, 0);
    final imminent = DateTime(2026, 10, 27, 9, 10);
    final plan = _plan(
      [_session(startsAt: past), _session(startsAt: imminent)],
      now,
    );
    expect(plan.reminders, isEmpty);
  });

  test('ملخص الغد يُجدول الثامنة مساءً ويحمل عدد المحاضرات', () {
    final tomorrow = DateTime(2026, 10, 28, 8, 30);
    final tomorrow2 = DateTime(2026, 10, 28, 10, 0);
    final plan = _plan(
      [_session(startsAt: tomorrow), _session(startsAt: tomorrow2)],
      now,
    );

    final digest = plan.reminders.firstWhere((row) => row.id == 9000);
    expect(digest.at, DateTime(2026, 10, 27, 20, 0));
    expect(digest.title, 'محاضرات الغد');
    expect(digest.body, startsWith('2 محاضرة'));
  });

  test('بعد الثامنة مساءً يُجدول الملخص غداً', () {
    final lateNow = DateTime(2026, 10, 27, 21, 0);
    final dayAfter = DateTime(2026, 10, 29, 9, 0);
    final plan = _plan([_session(startsAt: dayAfter)], lateNow);

    final digest = plan.reminders.firstWhere((row) => row.id == 9000);
    expect(digest.at, DateTime(2026, 10, 28, 20, 0));
  });

  test('لا ملخص إن لم توجد محاضرات غداً', () {
    final plan = _plan(const [], now);
    expect(plan.reminders, isEmpty);
    expect(plan.isEmpty, isTrue);
  });

  test('المعرّفات متتابعة والتذكيرات مرتبة زمنياً', () {
    final plan = _plan(
      [
        _session(startsAt: DateTime(2026, 10, 27, 12, 0)),
        _session(startsAt: DateTime(2026, 10, 27, 10, 0)),
        _session(startsAt: DateTime(2026, 10, 27, 14, 0)),
      ],
      now,
    );
    expect(plan.reminders.map((row) => row.at).toList(), orderedEquals([
      DateTime(2026, 10, 27, 9, 45),
      DateTime(2026, 10, 27, 11, 45),
      DateTime(2026, 10, 27, 13, 45),
    ]));
    expect(plan.reminders.map((row) => row.id).toSet(), hasLength(3));
  });
}
