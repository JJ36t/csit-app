import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/core/network/api_client.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/features/grades/data/grades_api.dart';
import 'package:csit/features/grades/presentation/grades_page.dart';
import 'package:csit/l10n/app_localizations.dart';

import 'academic_fakes.dart';
import 'attendance_fakes.dart';

GradeCourse _course() => const GradeCourse(
      offeringId: 'offer-1',
      courseCode: 'CS101',
      courseNameAr: 'مقدمة في علوم الحاسوب',
      assessments: [
        GradeAssessment(
          assessmentId: 'a1',
          name: 'الامتحان النصفي',
          kind: 'midterm',
          maxScore: 50,
          weight: 25,
          score: 40,
        ),
        GradeAssessment(
          assessmentId: 'a2',
          name: 'كويز 1',
          kind: 'quiz',
          maxScore: 10,
          weight: 5,
        ),
      ],
      weightedTotal: 20,
      weightSum: 30,
    );

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('ar'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    );

Future<void> _pump(WidgetTester tester, FakeGradesApi api) async {
  tester.view.physicalSize = const Size(1170, 3300);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(_wrap(GradesPage(
    api: api,
    session: SessionController(StubAuthApi()),
  )));
}

void main() {
  testWidgets('تعرض التقييمات والدرجات والمجموع الموزون', (tester) async {
    final api = FakeGradesApi(courses: [_course()]);
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(api.calls, 1);
    expect(find.text('مقدمة في علوم الحاسوب'), findsOneWidget);
    expect(find.byKey(const Key('weightedTotal-offer-1')), findsOneWidget);
    expect(find.text('20 من 30'), findsOneWidget);
    expect(find.textContaining('الامتحان النصفي'), findsOneWidget);
    expect(find.text('40 / 50'), findsOneWidget);
    expect(find.text('لم تُرصد'), findsOneWidget);
  });

  testWidgets('مادة بلا تقييمات منشورة تُظهر رسالة فراغ', (tester) async {
    final api = FakeGradesApi(courses: [
      const GradeCourse(
        offeringId: 'offer-2',
        courseCode: 'CS102',
        courseNameAr: 'هياكل البيانات',
        assessments: [],
        weightedTotal: 0,
        weightSum: 0,
      ),
    ]);
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(find.text('لا درجات منشورة بعد'), findsOneWidget);
    expect(find.text('0 من 0'), findsOneWidget);
  });

  testWidgets('لا مواد مسجَّلة تُظهر رسالة عامة', (tester) async {
    final api = FakeGradesApi(courses: const []);
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(find.text('لا توجد مواد دراسية مسجَّلة'), findsOneWidget);
  });

  testWidgets('فشل التحميل يعرض إعادة المحاولة ثم تنجح', (tester) async {
    final api = FakeGradesApi(error: ApiException('network_unreachable', null));
    await _pump(tester, api);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('gradesRetry')), findsOneWidget);

    api.error = null;
    api.courses = [_course()];
    await tester.tap(find.byKey(const Key('gradesRetry')));
    await tester.pumpAndSettle();

    expect(find.text('مقدمة في علوم الحاسوب'), findsOneWidget);
  });
}
