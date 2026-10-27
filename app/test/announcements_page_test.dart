import 'package:csit/core/network/api_client.dart';
import 'package:csit/features/announcements/data/announcements_api.dart';
import 'package:csit/features/announcements/presentation/announcements_page.dart';
import 'package:csit/features/auth/data/auth_repository.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _AuthStub implements AuthApi {
  @override
  Future<UserProfile> login({
    required String universityId,
    required String password,
    String? totpCode,
  }) async =>
      throw ApiException('unused', null);

  @override
  Future<UserProfile> me() async => throw ApiException('unused', null);

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {}

  @override
  Future<void> logout() async {}

  @override
  Future<bool> hasSession() async => false;
}

class _AnnouncementsStub implements AnnouncementsApi {
  _AnnouncementsStub(this.data);

  AnnouncementsData data;
  final List<String> marked = [];

  @override
  Future<AnnouncementsData> load() async => data;

  @override
  Future<void> markRead(String announcementId) async {
    marked.add(announcementId);
  }
}

AnnouncementItem _item({
  String id = 'a-1',
  String title = 'بدء المحاضرات',
  bool isRead = false,
}) =>
    AnnouncementItem(
      id: id,
      title: title,
      body: 'تنتظم المحاضرات اعتباراً من يوم الأحد.',
      priority: 'normal',
      pinned: false,
      isRead: isRead,
      publishedAt: DateTime.utc(2026, 10, 27, 8),
    );

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('ar'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    );

void main() {
  testWidgets('تعرض الإعلانات وتعلّم المقروء عند الفتح', (tester) async {
    final api = _AnnouncementsStub(
      AnnouncementsData(
        items: [_item()],
        fetchedAt: DateTime.utc(2026, 10, 27, 8),
      ),
    );
    await tester.pumpWidget(
      _wrap(AnnouncementsPage(api: api, session: SessionController(_AuthStub()))),
    );
    await tester.pumpAndSettle();

    expect(find.text('بدء المحاضرات'), findsOneWidget);

    await tester.tap(find.text('بدء المحاضرات'));
    await tester.pumpAndSettle();

    expect(find.text('تنتظم المحاضرات اعتباراً من يوم الأحد.'), findsWidgets);
    expect(api.marked, contains('a-1'));
    // النافذة مفتوحة الآن؛ أغلقها لتنتهي الحركة
    await tester.tapAt(const Offset(10, 10));
    await tester.pumpAndSettle();
  });

  testWidgets('البيانات المحفوظة تُعرض مع لافتة انقطاع', (tester) async {
    final api = _AnnouncementsStub(
      AnnouncementsData(
        items: [_item(id: 'a-2', title: 'خبر محفوظ')],
        fetchedAt: DateTime.utc(2026, 10, 27, 7),
        fromCache: true,
      ),
    );
    await tester.pumpWidget(
      _wrap(AnnouncementsPage(api: api, session: SessionController(_AuthStub()))),
    );
    await tester.pumpAndSettle();

    expect(find.text('خبر محفوظ'), findsOneWidget);
    expect(
      find.textContaining('تعذر الاتصال؛ تُعرض بيانات محفوظة'),
      findsOneWidget,
    );
  });

  testWidgets('قائمة فارغة تُظهر رسالة واضحة', (tester) async {
    final api = _AnnouncementsStub(const AnnouncementsData(items: []));
    await tester.pumpWidget(
      _wrap(AnnouncementsPage(api: api, session: SessionController(_AuthStub()))),
    );
    await tester.pumpAndSettle();

    expect(find.text('لا إعلانات منشورة حالياً'), findsOneWidget);
  });
}
