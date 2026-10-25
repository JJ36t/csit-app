import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/core/network/api_client.dart';
import 'package:csit/features/attendance/data/attendance_api.dart';
import 'package:csit/features/attendance/presentation/live_session_page.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/l10n/app_localizations.dart';

import 'attendance_fakes.dart';

const _sessionId = '3fa85f64-5717-4562-b3fc-2c963f66afa6';
const _token = '1761234567.abcdef0123456789';

const _threeStudents = [
  LiveStudent(
    universityId: '202310401',
    fullNameAr: 'أحمد ناصر',
    status: 'present',
  ),
  LiveStudent(
    universityId: '202310455',
    fullNameAr: 'تارة علي',
    status: 'late',
    flagged: true,
  ),
  LiveStudent(universityId: '202310489', fullNameAr: 'سجاد رعد'),
];

SessionSummary _summary({String status = 'scheduled'}) => SessionSummary(
      sessionId: _sessionId,
      date: DateTime.now().toUtc(),
      startsAt: DateTime.now().toUtc(),
      endsAt: DateTime.now().toUtc().add(const Duration(minutes: 90)),
      courseCode: 'CS301',
      courseNameAr: 'شبكات الحاسوب',
      kind: 'theory',
      room: 'قاعة 108',
      status: status,
    );

LiveSessionData _live({
  required String status,
  LiveQr? qr,
  List<LiveStudent> students = const [],
  Map<String, int> counts = const {},
}) =>
    LiveSessionData(
      sessionId: _sessionId,
      status: status,
      startsAt: DateTime.now().toUtc(),
      endsAt: DateTime.now().toUtc().add(const Duration(minutes: 90)),
      qr: qr,
      counts: counts,
      students: students,
    );

Widget _wrap(Widget child) {
  return MaterialApp(
    locale: const Locale('ar'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: child,
  );
}

/// مقاس هاتف عمودي (390×1100 منطقية) كي تُبنى بطاقة القائمة في الشجرة.
Future<void> _pumpLive(
  WidgetTester tester,
  FakeAttendanceApi api, {
  String status = 'scheduled',
}) async {
  tester.view.physicalSize = const Size(1170, 3300);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(_wrap(LiveSessionPage(
    summary: _summary(status: status),
    api: api,
    session: SessionController(StubAuthApi()),
    pollInterval: null,
  )));
}

void main() {
  testWidgets('الجلسة المفتوحة تعرض العدّاد والرمز وقائمة الحاضرين',
      (tester) async {
    final api = FakeAttendanceApi(liveResponses: [
      _live(
        status: 'open',
        qr: const LiveQr(token: _token, rotationS: 20, expiresIn: 18),
        students: _threeStudents,
        counts: {'present': 1, 'late': 1},
      ),
    ]);
    await _pumpLive(tester, api, status: 'open');
    await tester.pumpAndSettle();

    expect(api.liveCalls, 1);
    expect(find.byKey(const Key('qrView')), findsOneWidget);

    final counter =
        tester.widget<Text>(find.byKey(const Key('liveCounter')));
    expect(counter.data, '1 حاضراً من 3');

    expect(find.text('مشكوك 1'), findsOneWidget);
    expect(find.text('غائب 1'), findsOneWidget);

    expect(find.text('أحمد ناصر'), findsOneWidget);
    expect(find.text('تارة علي'), findsOneWidget);
    expect(find.text('سجاد رعد'), findsOneWidget);
  });

  testWidgets('الجلسة المجدولة: زر الفتح يفتحها ثم يظهر الرمز', (tester) async {
    final api = FakeAttendanceApi(liveResponses: [
      _live(status: 'scheduled', students: _threeStudents),
      _live(
        status: 'open',
        qr: const LiveQr(token: _token, rotationS: 20, expiresIn: 18),
        students: _threeStudents,
      ),
    ]);
    await _pumpLive(tester, api);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('openSessionButton')), findsOneWidget);
    expect(find.byKey(const Key('qrView')), findsNothing);

    await tester.tap(find.byKey(const Key('openSessionButton')));
    await tester.pumpAndSettle();

    expect(api.openCalls, 1);
    expect(find.byKey(const Key('qrView')), findsOneWidget);
    expect(find.byKey(const Key('openSessionButton')), findsNothing);
  });

  testWidgets('إغلاق الجلسة يمر بتأكيد ثم يعرض الغياب المسجَّل', (tester) async {
    final api = FakeAttendanceApi(
      liveResponses: [
        _live(
          status: 'open',
          qr: const LiveQr(token: _token, rotationS: 20, expiresIn: 18),
          students: _threeStudents,
        ),
        _live(status: 'closed', students: _threeStudents, counts: {'absent': 2}),
      ],
      closeResult: const CloseResult(absentMarked: 2, counts: {'absent': 2}),
    );
    await _pumpLive(tester, api, status: 'open');
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('closeSessionButton')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('closeConfirm')), findsOneWidget);

    await tester.tap(find.byKey(const Key('closeConfirm')));
    await tester.pumpAndSettle();

    expect(api.closeCalls, 1);
    expect(
      find.text('سُجّل غياب 2 طالباً لم يسجّلوا حضورهم.'),
      findsOneWidget,
    );
    expect(find.byKey(const Key('qrView')), findsNothing);
    expect(find.byKey(const Key('closeSessionButton')), findsNothing);
  });

  testWidgets('تصفية «حاضر» تُظهر الحاضرين فقط', (tester) async {
    final api = FakeAttendanceApi(liveResponses: [
      _live(
        status: 'open',
        qr: const LiveQr(token: _token, rotationS: 20, expiresIn: 18),
        students: _threeStudents,
      ),
    ]);
    await _pumpLive(tester, api, status: 'open');
    await tester.pumpAndSettle();

    await tester.tap(find.text('حاضر (1)'));
    await tester.pumpAndSettle();

    expect(find.text('أحمد ناصر'), findsOneWidget);
    expect(find.text('تارة علي'), findsNothing);
    expect(find.text('سجاد رعد'), findsNothing);
  });

  testWidgets('فشل التحميل يعرض إعادة المحاولة ثم تنجح', (tester) async {
    final api = FakeAttendanceApi(
      liveError: ApiException('network_unreachable', null),
    );
    await _pumpLive(tester, api);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('liveRetry')), findsOneWidget);

    // تعافي الشبكة ثم إعادة المحاولة من الزر.
    api.liveError = null;
    api.enqueueLive(_live(status: 'scheduled', students: _threeStudents));
    await tester.tap(find.byKey(const Key('liveRetry')));
    await tester.pumpAndSettle();

    expect(api.liveCalls, 2);
    expect(find.byKey(const Key('liveRetry')), findsNothing);
    expect(find.text('أحمد ناصر'), findsOneWidget);
  });
}
