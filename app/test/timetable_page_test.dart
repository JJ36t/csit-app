import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/core/network/api_client.dart';
import 'package:csit/core/utils/date_utils.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/features/timetable/data/timetable_api.dart';
import 'package:csit/features/timetable/presentation/timetable_page.dart';
import 'package:csit/l10n/app_localizations.dart';

import 'academic_fakes.dart';
import 'attendance_fakes.dart';

SessionItem _session({
  required String id,
  required String course,
  required DateTime start,
  String room = 'قاعة 108',
  String kind = 'theory',
  String status = 'scheduled',
}) =>
    SessionItem(
      sessionId: id,
      offeringId: 'offering-1',
      date: start,
      startsAt: start,
      endsAt: start.add(const Duration(minutes: 90)),
      courseCode: 'CS301',
      courseNameAr: course,
      kind: kind,
      room: room,
      status: status,
    );

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('ar'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    );

Future<void> _pump(WidgetTester tester, FakeTimetableApi api) async {
  tester.view.physicalSize = const Size(1170, 3300);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(_wrap(TimetablePage(
    api: api,
    session: SessionController(StubAuthApi()),
  )));
}

void main() {
  testWidgets('تعرض محاضرات اليوم مع الوقت والقاعة', (tester) async {
    // وقت ثابت بتوقيت بغداد (09:00) كي لا يعبر الاختبار منتصف الليل
    final baghdad = DateTime.now().toUtc().add(const Duration(hours: 3));
    final now = DateTime.utc(baghdad.year, baghdad.month, baghdad.day, 6, 0);
    final api = FakeTimetableApi(
      data: TimetableData(
        sessions: [
          _session(id: 's1', course: 'قواعد البيانات', start: now),
          _session(
            id: 's2',
            course: 'شبكات الحاسوب',
            start: now.add(const Duration(hours: 2)),
            room: 'قاعة 204',
            kind: 'lab',
          ),
        ],
        changes: const [],
      ),
    );
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(api.calls, 1);
    expect(find.text('قواعد البيانات'), findsOneWidget);
    expect(find.text('شبكات الحاسوب'), findsOneWidget);
    expect(find.text('قاعة 204 · مختبر'), findsOneWidget);
  });

  testWidgets('التنقل بين الأيام يعرض محاضرات اليوم المختار', (tester) async {
    final now = DateTime.now().toUtc();
    final tomorrow = now.add(const Duration(days: 1));
    final api = FakeTimetableApi(
      data: TimetableData(
        sessions: [
          _session(id: 's1', course: 'قواعد البيانات', start: now),
          _session(id: 's2', course: 'هياكل البيانات', start: tomorrow),
        ],
        changes: const [],
      ),
    );
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(find.text('هياكل البيانات'), findsNothing);

    // شريحة الغد كما يحسبها الجدول (يوم بتوقيت بغداد)
    final localTomorrow = toBaghdad(DateTime.now().toUtc()).add(const Duration(days: 1));
    final dayKey = DateTime.utc(localTomorrow.year, localTomorrow.month, localTomorrow.day);
    await tester.tap(find.byKey(Key('dayChip-${dayKey.toIso8601String()}')));
    await tester.pumpAndSettle();

    expect(find.text('هياكل البيانات'), findsOneWidget);
    expect(find.text('قواعد البيانات'), findsNothing);
  });

  testWidgets('بيانات محفوظة تظهر مع لافتة انقطاع الشبكة', (tester) async {
    final saved = DateTime.now().toUtc().subtract(const Duration(hours: 3));
    final api = FakeTimetableApi(
      data: TimetableData(
        sessions: [
          _session(
            id: 's1',
            course: 'قواعد البيانات',
            start: DateTime.now().toUtc(),
          ),
        ],
        changes: const [],
        fetchedAt: saved,
        fromCache: true,
      ),
    );
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('timetableOfflineBanner')), findsOneWidget);
    expect(find.text('قواعد البيانات'), findsOneWidget);
  });

  testWidgets('لا محاضرات تُظهر رسالة الفراغ', (tester) async {
    final api = FakeTimetableApi(
      data: const TimetableData(sessions: [], changes: []),
    );
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(find.text('لا توجد محاضرات في هذه الفترة'), findsOneWidget);
  });

  testWidgets('فشل التحميل يعرض إعادة المحاولة ثم تنجح', (tester) async {
    final api = FakeTimetableApi(
      error: ApiException('network_unreachable', null),
    );
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('timetableRetry')), findsOneWidget);

    api.error = null;
    api.data = TimetableData(
      sessions: [
        _session(id: 's1', course: 'قواعد البيانات', start: DateTime.now().toUtc()),
      ],
      changes: const [],
    );
    await tester.tap(find.byKey(const Key('timetableRetry')));
    await tester.pumpAndSettle();

    expect(find.text('قواعد البيانات'), findsOneWidget);
  });
}
