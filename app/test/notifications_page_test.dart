import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/core/network/api_client.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/features/notifications/data/notifications_api.dart';
import 'package:csit/features/notifications/presentation/notifications_page.dart';
import 'package:csit/l10n/app_localizations.dart';

import 'attendance_fakes.dart';
import 'engagement_fakes.dart';

const _unreadOne = NotificationItem(
  notificationId: 'n-1',
  type: 'announcement',
  title: 'إعلان جديد في القسم',
  body: 'نُشر إعلان جديد يخص مرحلتك.',
  isRead: false,
  createdAt: null,
);

const _unreadTwo = NotificationItem(
  notificationId: 'n-2',
  type: 'attendance',
  title: 'تم تسجيل حضورك',
  body: 'سُجّل حضورك في محاضرة الشبكات.',
  isRead: false,
  createdAt: null,
);

const _read = NotificationItem(
  notificationId: 'n-3',
  type: 'general',
  title: 'تحديث التطبيق',
  body: 'يتوفر إصدار جديد من التطبيق.',
  isRead: true,
  createdAt: null,
);

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('ar'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    );

Future<void> _pump(WidgetTester tester, FakeNotificationsApi api) async {
  tester.view.physicalSize = const Size(1170, 3300);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(_wrap(NotificationsPage(
    api: api,
    session: SessionController(StubAuthApi()),
  )));
}

void main() {
  testWidgets('يعرض الصندوق وعدد غير المقروء كما يعيده الخادم', (tester) async {
    final api = FakeNotificationsApi(
      items: const [_unreadOne, _unreadTwo, _read],
    );
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(api.inboxCalls, 1);
    expect(find.byKey(const Key('notificationsUnreadChip')), findsOneWidget);
    expect(find.text('2 غير مقروء'), findsOneWidget);
    expect(find.text('إعلان جديد في القسم'), findsOneWidget);
    expect(find.byKey(const Key('notificationUnread-n-1')), findsOneWidget);
    expect(find.byKey(const Key('notificationUnread-n-3')), findsNothing);
  });

  testWidgets('تعليم إشعار واحد بالنقر يحدّث العدد والشارة', (tester) async {
    final api = FakeNotificationsApi(items: const [_unreadOne, _unreadTwo]);
    await _pump(tester, api);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('notificationTile-n-1')));
    await tester.pumpAndSettle();

    expect(api.readIds, ['n-1']);
    expect(find.byKey(const Key('notificationUnread-n-1')), findsNothing);
    expect(find.byKey(const Key('notificationUnread-n-2')), findsOneWidget);
    expect(find.text('1 غير مقروء'), findsOneWidget);
  });

  testWidgets('تعليم الكل مقروءاً يفرّغ العدد ويعرض تأكيداً', (tester) async {
    final api = FakeNotificationsApi(items: const [_unreadOne, _unreadTwo]);
    await _pump(tester, api);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('markAllReadButton')));
    await tester.pumpAndSettle();

    expect(api.markAllCalls, 1);
    expect(find.byKey(const Key('notificationUnread-n-1')), findsNothing);
    expect(find.byKey(const Key('notificationUnread-n-2')), findsNothing);
    expect(find.byKey(const Key('notificationsUnreadChip')), findsNothing);
    expect(find.text('تم تعليم كل الإشعارات مقروءة'), findsOneWidget);
  });

  testWidgets('زر تعليم الكل معطّل حين لا يوجد غير مقروء', (tester) async {
    final api = FakeNotificationsApi(items: const [_read]);
    await _pump(tester, api);
    await tester.pumpAndSettle();

    final button = tester.widget<IconButton>(
      find.byKey(const Key('markAllReadButton')),
    );
    expect(button.onPressed, isNull);
  });

  testWidgets('صندوق فارغ يُظهر حالة فراغ عربية', (tester) async {
    final api = FakeNotificationsApi(items: const []);
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('notificationsEmpty')), findsOneWidget);
    expect(find.text('لا إشعارات بعد'), findsOneWidget);
  });

  testWidgets('فشل التحميل يعرض إعادة المحاولة ثم تنجح', (tester) async {
    final api = FakeNotificationsApi(
      items: const [_unreadOne],
      error: ApiException('network_unreachable', null),
    );
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('notificationsRetry')), findsOneWidget);

    api.error = null;
    await tester.tap(find.byKey(const Key('notificationsRetry')));
    await tester.pumpAndSettle();

    expect(find.text('إعلان جديد في القسم'), findsOneWidget);
  });

  testWidgets('التمرير للأسفل يعيد جلب الصندوق', (tester) async {
    final api = FakeNotificationsApi(items: const [_read]);
    await _pump(tester, api);
    await tester.pumpAndSettle();
    expect(api.inboxCalls, 1);

    api.items = const [_unreadOne];
    api.unreadCount = 1;
    await tester.fling(find.byType(ListView), const Offset(0, 320), 1000);
    await tester.pumpAndSettle();

    expect(api.inboxCalls, 2);
    expect(find.text('إعلان جديد في القسم'), findsOneWidget);
  });
}
