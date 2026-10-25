import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/core/network/api_client.dart';
import 'package:csit/features/attendance/data/attendance_api.dart';
import 'package:csit/features/attendance/data/location_service.dart';
import 'package:csit/features/attendance/data/qr_payload.dart';
import 'package:csit/features/attendance/presentation/scan_page.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/l10n/app_localizations.dart';

import 'attendance_fakes.dart';

const _sessionId = '3fa85f64-5717-4562-b3fc-2c963f66afa6';
const _token = '1761234567.abcdef0123456789';
final _validQr = const QrPayload(sessionId: _sessionId, token: _token).encode();

Widget _wrap(Widget child) {
  return MaterialApp(
    locale: const Locale('ar'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: child,
  );
}

/// مقاس هاتف عمودي (390×1000 منطقية) كي تُبنى كل عناصر القائمة في الشجرة:
/// ListView يبني أبناءه بكسل، والنافذة الافتراضية 800×600 أفقية.
void _usePhoneSurface(WidgetTester tester) {
  tester.view.physicalSize = const Size(1170, 3000);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.reset);
}

Future<void> _pumpPage(
  WidgetTester tester, {
  required FakeAttendanceApi api,
  required SessionController session,
  required FakeScanner scanner,
  LocationService? locationService,
}) async {
  _usePhoneSurface(tester);
  await tester.pumpWidget(_wrap(ScanPage(
    api: api,
    session: session,
    scanner: scanner,
    locationService: locationService ?? FakeLocationService(),
  )));
}

void main() {
  testWidgets('المسح الناجح يعرض «حاضر» ورسالة الخادم', (tester) async {
    final api = FakeAttendanceApi();
    final scanner = FakeScanner();
    final session = SessionController(StubAuthApi());
    await _pumpPage(tester, api: api, session: session, scanner: scanner);

    scanner.emit(_validQr);
    await tester.pumpAndSettle();

    expect(api.scanCalls, 1);
    expect(api.lastSessionId, _sessionId);
    expect(api.lastToken, _token);
    expect(find.byKey(const Key('scanResultCard')), findsOneWidget);
    final title = tester.widget<Text>(find.byKey(const Key('scanResultTitle')));
    expect(title.data, 'حاضر');
    expect(find.text('تم تسجيل حضورك'), findsOneWidget);
  });

  testWidgets('المسح المشكوك يعرض السبب بوصفه العربي', (tester) async {
    final api = FakeAttendanceApi(
      scanResult: const ScanResult(
        attendanceId: 'att-2',
        status: 'late',
        flagged: true,
        flagReason: 'outside_campus:120m',
        messageAr: 'تم تسجيل حضورك (قيد المراجعة لخروج الموقع عن النطاق)',
      ),
    );
    final scanner = FakeScanner();
    final session = SessionController(StubAuthApi());
    await _pumpPage(tester, api: api, session: session, scanner: scanner);

    scanner.emit(_validQr);
    await tester.pumpAndSettle();

    final title = tester.widget<Text>(find.byKey(const Key('scanResultTitle')));
    expect(title.data, 'مشكوك');
    expect(
      find.text('الموقع خارج نطاق القاعة (نحو 120م)؛ سيراجع التدريسي الحضور'),
      findsOneWidget,
    );
    expect(find.byKey(const Key('scanFlagReason')), findsOneWidget);
  });

  testWidgets('رمز غير صالح يُرفض محلياً ولا يصل الخادم', (tester) async {
    final api = FakeAttendanceApi();
    final scanner = FakeScanner();
    final session = SessionController(StubAuthApi());
    await _pumpPage(tester, api: api, session: session, scanner: scanner);

    scanner.emit('كود عشوائي ليس رمز حضور');
    await tester.pumpAndSettle();

    expect(api.scanCalls, 0);
    expect(find.byKey(const Key('scanError')), findsOneWidget);
    expect(
      find.text('الرمز الممسوح ليس رمز حضور صالحاً لهذا التطبيق'),
      findsOneWidget,
    );
  });

  testWidgets('رمز منتهٍ (410) يعرض رسالة الخادم العربية', (tester) async {
    final api = FakeAttendanceApi(
      scanError: ApiException(
        'token_expired',
        'انتهت صلاحية رمز الحضور؛ امسح الرمز الجديد',
        statusCode: 410,
      ),
    );
    final scanner = FakeScanner();
    final session = SessionController(StubAuthApi());
    await _pumpPage(tester, api: api, session: session, scanner: scanner);

    scanner.emit(_validQr);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('scanError')), findsOneWidget);
    expect(find.text('انتهت صلاحية رمز الحضور؛ امسح الرمز الجديد'),
        findsOneWidget);
  });

  testWidgets('خطأ الشبكة يعرض نص الترجمة لا رمز الخطأ', (tester) async {
    final api = FakeAttendanceApi(
      scanError: ApiException('network_unreachable', null),
    );
    final scanner = FakeScanner();
    final session = SessionController(StubAuthApi());
    await _pumpPage(tester, api: api, session: session, scanner: scanner);

    scanner.emit(_validQr);
    await tester.pumpAndSettle();

    expect(
      find.text('تعذر الاتصال بالخادم؛ تحقق من الإنترنت وحاول مجدداً'),
      findsOneWidget,
    );
  });

  testWidgets('غياب معرّف الجهاز يطالب بإعادة الدخول', (tester) async {
    final api = FakeAttendanceApi(
      scanError: ApiException('missing_device_id', null),
    );
    final scanner = FakeScanner();
    final session = SessionController(StubAuthApi());
    await _pumpPage(tester, api: api, session: session, scanner: scanner);

    scanner.emit(_validQr);
    await tester.pumpAndSettle();

    expect(
      find.text('معلومات جهازك غير مكتملة؛ سجّل الدخول من جديد ثم أعد المحاولة'),
      findsOneWidget,
    );
  });

  testWidgets('الموقع المتاح يُرفَق بطلب المسح', (tester) async {
    final api = FakeAttendanceApi();
    final scanner = FakeScanner();
    final location = FakeLocationService(
      const ScanLocation(lat: 31.9901, lng: 44.9201, accuracyM: 12),
    );
    final session = SessionController(StubAuthApi());
    await _pumpPage(
      tester,
      api: api,
      session: session,
      scanner: scanner,
      locationService: location,
    );

    scanner.emit(_validQr);
    await tester.pumpAndSettle();

    expect(api.lastLocation, isNotNull);
    expect(api.lastLocation!.lat, 31.9901);
    expect(api.lastLocation!.lng, 44.9201);
  });

  testWidgets('انتهاء الجلسة (401) يُفرغ الجلسة ويُعاد للدخول', (tester) async {
    final api = FakeAttendanceApi(
      scanError: ApiException('session_expired', null, statusCode: 401),
    );
    final scanner = FakeScanner();
    final session = SessionController(StubAuthApi());
    await session.login(universityId: '20240001', password: 'x');
    expect(session.isAuthenticated, isTrue);

    await _pumpPage(tester, api: api, session: session, scanner: scanner);
    scanner.emit(_validQr);
    await tester.pumpAndSettle();

    expect(session.isAuthenticated, isFalse);
  });
}
