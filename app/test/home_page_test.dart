import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/core/app_services.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/features/home/presentation/home_page.dart';
import 'package:csit/features/notifications/data/notifications_api.dart';
import 'package:csit/l10n/app_localizations.dart';

import 'academic_fakes.dart';
import 'attendance_fakes.dart';
import 'engagement_fakes.dart';

AppServices _services({
  FakeAnnouncementsApi? announcements,
  FakeNotificationsApi? notifications,
}) =>
    AppServices(
      auth: StubAuthApi(),
      attendance: FakeAttendanceApi(),
      timetable: FakeTimetableApi(),
      materials: FakeMaterialsApi(),
      grades: FakeGradesApi(),
      announcements: announcements ?? FakeAnnouncementsApi(),
      notifications: notifications ?? FakeNotificationsApi(),
    );

Future<SessionController> _signedIn() async {
  final session = SessionController(StubAuthApi());
  await session.login(universityId: '20240001', password: 'secret');
  return session;
}

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('ar'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    );

Future<void> _pump(
  WidgetTester tester,
  AppServices services,
  SessionController session,
) async {
  tester.view.physicalSize = const Size(1170, 3300);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    _wrap(HomePage(session: session, services: services)),
  );
}

void main() {
  testWidgets('بطاقة الإشعارات تعرض شارة عدد غير المقروء', (tester) async {
    final notifications = FakeNotificationsApi(
      items: const [
        NotificationItem(
          notificationId: 'n-1',
          type: 'announcement',
          title: 'إعلان',
          body: 'نص',
          isRead: false,
        ),
      ],
      unreadCount: 3,
    );
    await _pump(tester, _services(notifications: notifications), await _signedIn());
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('notificationsBadge')), findsOneWidget);
    expect(
      find.descendant(
        of: find.byKey(const Key('notificationsBadge')),
        matching: find.text('3'),
      ),
      findsOneWidget,
    );
  });

  testWidgets('لا شارة حين لا يوجد إشعار غير مقروء', (tester) async {
    final notifications = FakeNotificationsApi(unreadCount: 0);
    await _pump(tester, _services(notifications: notifications), await _signedIn());
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('notificationsBadge')), findsNothing);
  });

  testWidgets('بطاقة الإشعارات تفتح صندوق الوارد', (tester) async {
    final notifications = FakeNotificationsApi(unreadCount: 0);
    await _pump(tester, _services(notifications: notifications), await _signedIn());
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('notificationsCard')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('notificationsEmpty')), findsOneWidget);
  });

  testWidgets('بطاقة الإعلانات تفتح قائمة الإعلانات', (tester) async {
    await _pump(tester, _services(), await _signedIn());
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('announcementsCard')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('announcementsEmpty')), findsOneWidget);
  });

  testWidgets('بطاقة الملف الشخصي تفتح بيانات الحساب', (tester) async {
    await _pump(tester, _services(), await _signedIn());
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('profileCard')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('profileUniversityId')), findsOneWidget);
    expect(find.text(StubAuthApi.defaultProfile.fullNameAr), findsWidgets);
  });
}
