import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/features/auth/data/auth_repository.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/features/profile_settings/presentation/profile_page.dart';
import 'package:csit/l10n/app_localizations.dart';

import 'attendance_fakes.dart';

const _student = UserProfile(
  universityId: '20240001',
  fullNameAr: 'طالب تجريبي',
  role: 'student',
  mustChangePassword: false,
  departmentName: 'علوم الحاسوب',
  stage: 2,
  groupName: 'B',
);

const _instructor = UserProfile(
  universityId: 'T-77',
  fullNameAr: 'د. أحمد التدريسي',
  role: 'instructor',
  mustChangePassword: false,
  departmentName: 'علوم الحاسوب',
);

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('ar'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    );

Future<SessionController> _signedIn(UserProfile profile) async {
  final session = SessionController(StubAuthApi(profile: profile));
  await session.login(universityId: profile.universityId, password: 'secret');
  return session;
}

Future<void> _pump(WidgetTester tester, SessionController session) async {
  tester.view.physicalSize = const Size(1170, 3300);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(_wrap(ProfilePage(session: session)));
}

void main() {
  testWidgets('تعرض الاسم والرقم الجامعي والدور والقسم والمرحلة والشعبة',
      (tester) async {
    final session = await _signedIn(_student);
    await _pump(tester, session);
    await tester.pumpAndSettle();

    expect(find.text('طالب تجريبي'), findsOneWidget);
    expect(find.text('20240001'), findsOneWidget);
    expect(find.text('طالب'), findsOneWidget);
    expect(find.text('علوم الحاسوب'), findsOneWidget);
    expect(find.text('2'), findsOneWidget);
    expect(find.text('B'), findsOneWidget);
  });

  testWidgets('دور التدريسي يُعرض بالعربية', (tester) async {
    final session = await _signedIn(_instructor);
    await _pump(tester, session);
    await tester.pumpAndSettle();

    expect(find.text('تدريسي'), findsOneWidget);
    expect(find.byKey(const Key('profileStage')), findsNothing);
    expect(find.byKey(const Key('profileGroup')), findsNothing);
  });

  testWidgets('رابط تغيير كلمة المرور يفتح شاشتها', (tester) async {
    final session = await _signedIn(_student);
    await _pump(tester, session);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('profileChangePassword')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('currentPasswordField')), findsOneWidget);
    expect(find.byKey(const Key('newPasswordField')), findsOneWidget);
  });

  testWidgets('رابط الخروج ينهي الجلسة', (tester) async {
    final session = await _signedIn(_student);
    await _pump(tester, session);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('profileLogout')));
    await tester.pumpAndSettle();

    expect(session.isAuthenticated, isFalse);
    expect(session.profile, isNull);
  });
}
