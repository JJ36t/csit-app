import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/core/network/api_client.dart';
import 'package:csit/features/announcements/data/announcements_api.dart';
import 'package:csit/features/announcements/presentation/announcements_page.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/l10n/app_localizations.dart';

import 'attendance_fakes.dart';
import 'engagement_fakes.dart';

const _urgent = AnnouncementItem(
  announcementId: 'a-1',
  scope: 'college',
  title: 'تأجيل محاضرات يوم الأحد',
  body: 'نظراً لظروف الطقس تُؤجَّل محاضرات يوم الأحد إلى يوم الثلاثاء من الأسبوع نفسه.',
  priority: 'high',
  pinned: true,
  isRead: false,
  publishAt: null,
  createdAt: null,
);

const _normal = AnnouncementItem(
  announcementId: 'a-2',
  scope: 'department',
  title: 'فتح استمارة المختبر',
  body: 'تُفتح استمارة اختيار المجموعة المخبرية يوم الاثنين.',
  priority: 'normal',
  pinned: false,
  isRead: true,
  publishAt: null,
  createdAt: null,
);

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('ar'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    );

Future<void> _pump(WidgetTester tester, FakeAnnouncementsApi api) async {
  tester.view.physicalSize = const Size(1170, 3300);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(_wrap(AnnouncementsPage(
    api: api,
    session: SessionController(StubAuthApi()),
  )));
}

void main() {
  testWidgets('تعرض الإعلانات مع شريحة التثبيت والأولوية', (tester) async {
    final api = FakeAnnouncementsApi(items: const [_urgent, _normal]);
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(api.feedCalls, 1);
    expect(find.text('تأجيل محاضرات يوم الأحد'), findsOneWidget);
    expect(find.text('فتح استمارة المختبر'), findsOneWidget);
    expect(find.byKey(const Key('announcementPinned-a-1')), findsOneWidget);
    expect(find.byKey(const Key('announcementPriority-a-1')), findsOneWidget);
    expect(find.byKey(const Key('announcementUnread-a-1')), findsOneWidget);
    // الإعلان المقروء بلا شريحة تثبيت/أولوية وبلا نقطة «غير مقروء».
    expect(find.byKey(const Key('announcementPinned-a-2')), findsNothing);
    expect(find.byKey(const Key('announcementUnread-a-2')), findsNothing);
  });

  testWidgets('فتح الإعلان يعرض النص كاملاً ويعلّمه مقروءاً', (tester) async {
    final api = FakeAnnouncementsApi(items: const [_urgent]);
    await _pump(tester, api);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('announcementTile-a-1')));
    await tester.pumpAndSettle();

    expect(api.readIds, ['a-1']);
    expect(find.byKey(const Key('announcementDetailBody')), findsOneWidget);
    expect(
      find.text(
        'نظراً لظروف الطقس تُؤجَّل محاضرات يوم الأحد إلى يوم الثلاثاء من الأسبوع نفسه.',
      ),
      findsOneWidget,
    );

    await tester.tap(find.byType(BackButton));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('announcementUnread-a-1')), findsNothing);
  });

  testWidgets('الإعلان المقروء لا يُعلَّم مرة أخرى عند فتحه', (tester) async {
    final api = FakeAnnouncementsApi(items: const [_normal]);
    await _pump(tester, api);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('announcementTile-a-2')));
    await tester.pumpAndSettle();

    expect(api.readIds, isEmpty);
    expect(find.byKey(const Key('announcementDetailBody')), findsOneWidget);
  });

  testWidgets('قائمة فارغة تُظهر حالة فراغ عربية', (tester) async {
    final api = FakeAnnouncementsApi(items: const []);
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('announcementsEmpty')), findsOneWidget);
    expect(find.text('لا توجد إعلانات موجهة إليك'), findsOneWidget);
  });

  testWidgets('فشل التحميل يعرض إعادة المحاولة ثم تنجح', (tester) async {
    final api = FakeAnnouncementsApi(
      items: const [_urgent],
      error: ApiException('network_unreachable', null),
    );
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('announcementsRetry')), findsOneWidget);

    api.error = null;
    await tester.tap(find.byKey(const Key('announcementsRetry')));
    await tester.pumpAndSettle();

    expect(find.text('تأجيل محاضرات يوم الأحد'), findsOneWidget);
  });

  testWidgets('التمرير للأسفل يحدّث القائمة', (tester) async {
    final api = FakeAnnouncementsApi(items: const [_normal]);
    await _pump(tester, api);
    await tester.pumpAndSettle();
    expect(api.feedCalls, 1);

    api.items = const [_normal, _urgent];
    await tester.fling(find.byType(ListView), const Offset(0, 320), 1000);
    await tester.pumpAndSettle();

    expect(api.feedCalls, 2);
    expect(find.text('تأجيل محاضرات يوم الأحد'), findsOneWidget);
  });
}
