import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/core/network/api_client.dart';
import 'package:csit/features/auth/data/auth_repository.dart';
import 'package:csit/features/auth/presentation/login_page.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/l10n/app_localizations.dart';

/// بديل في الذاكرة عن الـAPI — الاختبارات لا تلمس الشبكة ولا التخزين الآمن.
class FakeAuthApi implements AuthApi {
  FakeAuthApi({this.loginError, UserProfile? profile}) : _profile = profile;

  ApiException? loginError;
  UserProfile? _profile;
  bool loggedOut = false;
  int loginCalls = 0;

  static const defaultProfile = UserProfile(
    universityId: '20240001',
    fullNameAr: 'طالب تجريبي',
    role: 'student',
    mustChangePassword: true,
    departmentName: 'علوم الحاسوب',
    stage: 1,
    groupName: 'A',
  );

  @override
  Future<bool> hasSession() async => false;

  @override
  Future<UserProfile> login({
    required String universityId,
    required String password,
  }) async {
    loginCalls++;
    final error = loginError;
    if (error != null) {
      throw error;
    }
    return _profile ??= defaultProfile;
  }

  @override
  Future<UserProfile> me() async {
    final profile = _profile;
    if (profile == null) {
      throw ApiException('not_authenticated', null, statusCode: 401);
    }
    return profile;
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {}

  @override
  Future<void> logout() async {
    loggedOut = true;
    _profile = null;
  }
}

Widget _wrap(Widget child) {
  return MaterialApp(
    locale: const Locale('ar'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: child,
  );
}

void main() {
  testWidgets('الحقول الفارغة تُظهر رسالة الإلزام ولا تُرسل', (tester) async {
    final api = FakeAuthApi();
    final session = SessionController(api);
    await tester.pumpWidget(_wrap(LoginPage(session: session)));

    await tester.tap(find.byKey(const Key('loginButton')));
    await tester.pumpAndSettle();

    expect(find.text('هذا الحقل مطلوب'), findsNWidgets(2));
    expect(api.loginCalls, 0);
    expect(session.isAuthenticated, isFalse);
  });

  testWidgets('الرقم الجامعي القصير يُرفض قبل الإرسال', (tester) async {
    final api = FakeAuthApi();
    final session = SessionController(api);
    await tester.pumpWidget(_wrap(LoginPage(session: session)));

    await tester.enterText(find.byKey(const Key('universityIdField')), '12');
    await tester.enterText(find.byKey(const Key('passwordField')), 'x');
    await tester.tap(find.byKey(const Key('loginButton')));
    await tester.pumpAndSettle();

    expect(find.text('الرقم الجامعي يجب أن يكون 3 محارف على الأقل'), findsOneWidget);
    expect(api.loginCalls, 0);
  });

  testWidgets('رسالة خطأ الخادم العربية تظهر للمستخدم', (tester) async {
    final api = FakeAuthApi(
      loginError: ApiException(
        'invalid_credentials',
        'الرقم الجامعي أو كلمة المرور غير صحيحة',
        statusCode: 401,
      ),
    );
    final session = SessionController(api);
    await tester.pumpWidget(_wrap(LoginPage(session: session)));

    await tester.enterText(find.byKey(const Key('universityIdField')), '20240001');
    await tester.enterText(find.byKey(const Key('passwordField')), 'wrong-password');
    await tester.tap(find.byKey(const Key('loginButton')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('loginError')), findsOneWidget);
    expect(find.text('الرقم الجامعي أو كلمة المرور غير صحيحة'), findsOneWidget);
    expect(session.isAuthenticated, isFalse);
  });

  testWidgets('خطأ الشبكة يعرض نص الترجمة بدل رسالة الخادم', (tester) async {
    final api = FakeAuthApi(loginError: ApiException('network_unreachable', null));
    final session = SessionController(api);
    await tester.pumpWidget(_wrap(LoginPage(session: session)));

    await tester.enterText(find.byKey(const Key('universityIdField')), '20240001');
    await tester.enterText(find.byKey(const Key('passwordField')), '20240001');
    await tester.tap(find.byKey(const Key('loginButton')));
    await tester.pumpAndSettle();

    expect(find.text('تعذر الاتصال بالخادم؛ تحقق من الإنترنت وحاول مجدداً'), findsOneWidget);
  });

  testWidgets('الدخول الناجح يحدّث الجلسة', (tester) async {
    final api = FakeAuthApi();
    final session = SessionController(api);
    await tester.pumpWidget(_wrap(LoginPage(session: session)));

    await tester.enterText(find.byKey(const Key('universityIdField')), '20240001');
    await tester.enterText(find.byKey(const Key('passwordField')), '20240001');
    await tester.tap(find.byKey(const Key('loginButton')));
    await tester.pumpAndSettle();

    expect(api.loginCalls, 1);
    expect(session.isAuthenticated, isTrue);
    expect(session.profile?.fullNameAr, 'طالب تجريبي');
    expect(session.profile?.departmentName, 'علوم الحاسوب');
  });
}
