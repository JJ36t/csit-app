import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/core/network/api_client.dart';
import 'package:csit/features/attendance/data/attendance_api.dart';
import 'package:csit/features/attendance/presentation/live_session_page.dart';
import 'package:csit/features/attendance/presentation/sessions_page.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/l10n/app_localizations.dart';

import 'attendance_fakes.dart';

SessionSummary _session({
  required String id,
  required String name,
  DateTime? startsAt,
  String status = 'scheduled',
}) {
  final start = startsAt ?? DateTime.now().toUtc();
  return SessionSummary(
    sessionId: id,
    date: start,
    startsAt: start,
    endsAt: start.add(const Duration(minutes: 90)),
    courseCode: 'CS301',
    courseNameAr: name,
    kind: 'theory',
    room: 'قاعة 108',
    status: status,
  );
}

Widget _wrap(Widget child) {
  return MaterialApp(
    locale: const Locale('ar'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: child,
  );
}

Future<void> _pumpSessions(WidgetTester tester, FakeAttendanceApi api) async {
  tester.view.physicalSize = const Size(1170, 3300);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(_wrap(SessionsPage(
    api: api,
    session: SessionController(StubAuthApi()),
    pollInterval: null,
  )));
}

void main() {
  testWidgets('تعرض حصص اليوم فقط وترتبها', (tester) async {
    final api = FakeAttendanceApi(sessions: [
      _session(id: 's-1', name: 'قواعد البيانات'),
      _session(id: 's-2', name: 'شبكات الحاسوب'),
      _session(
        id: 's-3',
        name: 'هياكل البيانات',
        startsAt: DateTime.now().toUtc().add(const Duration(days: 2)),
      ),
    ]);
    await _pumpSessions(tester, api);
    await tester.pumpAndSettle();

    expect(find.text('قواعد البيانات'), findsOneWidget);
    expect(find.text('شبكات الحاسوب'), findsOneWidget);
    expect(find.text('هياكل البيانات'), findsNothing);
    expect(find.byKey(const Key('sessionTile-s-1')), findsOneWidget);
    expect(find.byKey(const Key('sessionTile-s-3')), findsNothing);
  });

  testWidgets('لا حصص اليوم تُظهر رسالة الفراغ', (tester) async {
    final api = FakeAttendanceApi(sessions: const []);
    await _pumpSessions(tester, api);
    await tester.pumpAndSettle();

    expect(find.text('لا توجد حصص مجدولة لك اليوم'), findsOneWidget);
  });

  testWidgets('فشل التحميل يعرض إعادة المحاولة ثم تنجح', (tester) async {
    final api = FakeAttendanceApi(
      sessions: const [],
      sessionsError: ApiException('network_unreachable', null),
    );
    await _pumpSessions(tester, api);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('sessionsRetry')), findsOneWidget);

    api.sessionsError = null;
    await tester.tap(find.byKey(const Key('sessionsRetry')));
    await tester.pumpAndSettle();

    expect(find.text('لا توجد حصص مجدولة لك اليوم'), findsOneWidget);
  });

  testWidgets('النقر على حصة يفتح القائمة اللحظية', (tester) async {
    final api = FakeAttendanceApi(
      sessions: [_session(id: 's-9', name: 'شبكات الحاسوب')],
      liveResponses: [
        LiveSessionData(
          sessionId: 's-9',
          status: 'scheduled',
          startsAt: DateTime.now().toUtc(),
          endsAt: DateTime.now().toUtc().add(const Duration(minutes: 90)),
          counts: const {},
          students: const [],
        ),
      ],
    );
    await _pumpSessions(tester, api);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('sessionTile-s-9')));
    // تحميلات صريحة بدل pumpAndSettle لتفادي انتظار مؤشرات لا تنتهي.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));

    expect(find.byType(LiveSessionPage), findsOneWidget);
    expect(find.text('قائمة الحاضرين'), findsOneWidget);
  });
}
