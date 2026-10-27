import 'package:csit/features/auth/data/auth_repository.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/features/requests/data/requests_api.dart';
import 'package:csit/features/requests/presentation/requests_page.dart';
import 'package:csit/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _AuthStub implements AuthApi {
  _AuthStub(this.profile);

  final UserProfile? profile;

  @override
  Future<UserProfile> login({
    required String universityId,
    required String password,
    String? totpCode,
  }) async =>
      profile!;

  @override
  Future<UserProfile> me() async => profile!;

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {}

  @override
  Future<void> logout() async {}

  @override
  Future<bool> hasSession() async => profile != null;
}

class _RequestsStub implements RequestsApi {
  RequestDetail current = RequestDetail(
    summary: RequestSummary(
      id: 'r-1',
      category: 'academic',
      categoryLabel: 'مسألة أكاديمية',
      subject: 'طلب تأجيل اختبار',
      status: 'open',
      updatedAt: DateTime.utc(2026, 10, 27, 9),
    ),
    messages: [
      RequestMessageItem(
        id: 'm-1',
        senderId: 'student-1',
        body: 'أرجو تأجيل الاختبار.',
        createdAt: DateTime.utc(2026, 10, 27, 9),
      ),
    ],
  );

  int sent = 0;

  @override
  Future<List<RequestSummary>> list() async => [current.summary];

  @override
  Future<RequestDetail> detail(String requestId) async => current;

  @override
  Future<RequestDetail> create({
    required String category,
    required String subject,
    required String body,
  }) async =>
      current;

  @override
  Future<RequestDetail> sendMessage(String requestId, String body) async {
    sent++;
    current = RequestDetail(
      summary: current.summary,
      messages: [
        ...current.messages,
        RequestMessageItem(
          id: 'm-2',
          senderId: 'student-1',
          body: body,
          createdAt: DateTime.utc(2026, 10, 27, 10),
        ),
      ],
    );
    return current;
  }

  @override
  Future<void> updateRequest(
    String requestId, {
    String? status,
    String? assignedTo,
  }) async {}
}

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('ar'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    );

void main() {
  testWidgets('قائمة الطلبات تفتح المحادثة وترسل رداً', (tester) async {
    final api = _RequestsStub();
    final profile = const UserProfile(
      id: 'student-1',
      universityId: 'S-100',
      fullNameAr: 'علي حسن',
      role: 'student',
      mustChangePassword: false,
    );
    final session = SessionController(_AuthStub(profile));

    await tester.pumpWidget(_wrap(RequestsPage(api: api, session: session)));
    await tester.pumpAndSettle();

    expect(find.text('طلب تأجيل اختبار'), findsOneWidget);

    await tester.tap(find.text('طلب تأجيل اختبار'));
    await tester.pumpAndSettle();

    expect(find.text('أرجو تأجيل الاختبار.'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('replyField')), 'شكراً لكم');
    await tester.tap(find.byKey(const Key('sendReplyButton')));
    await tester.pumpAndSettle();

    expect(api.sent, 1);
    expect(find.text('شكراً لكم'), findsOneWidget);
  });

  testWidgets('الطلب المغلق يمنع الرد', (tester) async {
    final api = _RequestsStub();
    api.current = RequestDetail(
      summary: RequestSummary(
        id: 'r-1',
        category: 'documents',
        categoryLabel: 'وثيقة أو تأييد',
        subject: 'تأييد استمرار',
        status: 'resolved',
        updatedAt: DateTime.utc(2026, 10, 27, 9),
      ),
      messages: const [],
    );
    final session = SessionController(
      _AuthStub(
        const UserProfile(
          id: 'student-1',
          universityId: 'S-100',
          fullNameAr: 'علي حسن',
          role: 'student',
          mustChangePassword: false,
        ),
      ),
    );

    await tester.pumpWidget(_wrap(RequestsPage(api: api, session: session)));
    await tester.pumpAndSettle();
    await tester.tap(find.text('تأييد استمرار'));
    await tester.pumpAndSettle();

    expect(find.text('الطلب مغلق؛ لا يمكن إضافة رسائل'), findsOneWidget);
    expect(find.byKey(const Key('replyField')), findsNothing);
  });
}
