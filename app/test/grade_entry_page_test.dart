import 'package:csit/features/auth/data/auth_repository.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/features/grades/data/grade_entry_api.dart';
import 'package:csit/features/grades/presentation/grade_entry_page.dart';
import 'package:csit/features/materials/data/materials_api.dart';
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
  Future<bool> hasSession() async => true;
}

class _OfferingsStub implements MaterialsApi {
  @override
  Future<List<OfferingSummary>> myOfferings() async => const [
        OfferingSummary(
          offeringId: 'o-1',
          courseCode: 'CS203',
          courseNameAr: 'قواعد البيانات',
          kind: 'theory',
          stage: 2,
          groupName: 'A',
          studyType: 'morning',
        ),
      ];

  @override
  Future<MaterialsData> materials(String offeringId) async =>
      const MaterialsData(items: []);
}

class _GradeEntryStub implements GradeEntryApi {
  _GradeEntryStub({this.published = false});

  bool published;
  Map<String, double> saved = {};
  int publishCalls = 0;

  @override
  Future<OfferingGrades> load(String offeringId) async => OfferingGrades(
        offeringId: offeringId,
        courseCode: 'CS203',
        courseName: 'قواعد البيانات',
        assessments: [
          GradeAssessment(
            id: 'a-1',
            name: 'كوز 1',
            kind: 'quiz',
            maxScore: 20,
            weight: 15,
            isPublished: published,
          ),
        ],
        students: const [
          GradeStudentRow(
            studentId: 's-1',
            universityId: '202310401',
            fullName: 'أحمد ناصر',
            scores: {'a-1': 18},
            weightedTotal: 13.5,
            weightSum: 15,
          ),
          GradeStudentRow(
            studentId: 's-2',
            universityId: '202310428',
            fullName: 'براء سعد',
            scores: {},
            weightedTotal: 0,
            weightSum: 15,
          ),
        ],
      );

  @override
  Future<GradeAssessment> createAssessment({
    required String offeringId,
    required String name,
    required String kind,
    required double maxScore,
    required double weight,
  }) async =>
      GradeAssessment(
        id: 'a-2',
        name: name,
        kind: kind,
        maxScore: maxScore,
        weight: weight,
        isPublished: false,
      );

  @override
  Future<void> saveScores(String assessmentId, Map<String, double> scores) async {
    saved = scores;
  }

  @override
  Future<int> publish(String assessmentId) async {
    publishCalls++;
    published = true;
    return 2;
  }
}

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('ar'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    );

Future<SessionController> _session(String role) async {
  final session = SessionController(
    _AuthStub(
      UserProfile(
        id: 'u-1',
        universityId: 'T-101',
        fullNameAr: 'د. أحمد',
        role: role,
        mustChangePassword: false,
      ),
    ),
  );
  await session.restore();
  return session;
}

Future<void> _pumpPage(
  WidgetTester tester,
  GradeEntryApi api,
  String role,
) async {
  await tester.pumpWidget(
    _wrap(
      GradeEntryPage(
        api: api,
        offeringsApi: _OfferingsStub(),
        session: await _session(role),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('تعرض الدرجات المحفوظة وتحسب المدخلات', (tester) async {
    final api = _GradeEntryStub();
    await _pumpPage(tester, api, 'instructor');

    expect(find.textContaining('قواعد البيانات — كوز 1'), findsOneWidget);
    expect(find.text('أحمد ناصر'), findsOneWidget);
    expect(find.text('أُدخلت 1 من 2 درجة'), findsOneWidget);

    final field = find.byKey(const Key('scoreField-s-1'));
    expect((tester.widget<TextField>(field)).controller?.text, '18');
  });

  testWidgets('درجة تتجاوز العظمى تُظهر خطأً وتعطّل الحفظ', (tester) async {
    final api = _GradeEntryStub();
    await _pumpPage(tester, api, 'instructor');

    await tester.enterText(find.byKey(const Key('scoreField-s-2')), '22');
    await tester.pumpAndSettle();

    expect(find.text('الدرجة يجب أن تكون بين 0 و20'), findsOneWidget);
    final save = tester.widget<OutlinedButton>(
      find.byKey(const Key('saveDraftButton')),
    );
    expect(save.onPressed, isNull);
  });

  testWidgets('حفظ المسودة يرسل الدرجات الصحيحة', (tester) async {
    final api = _GradeEntryStub();
    await _pumpPage(tester, api, 'instructor');

    await tester.enterText(find.byKey(const Key('scoreField-s-2')), '15');
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('saveDraftButton')));
    await tester.pumpAndSettle();

    expect(api.saved, {'s-1': 18, 's-2': 15});
    expect(find.text('حُفظت المسودة'), findsOneWidget);
  });

  testWidgets('النشر معطّل للتدريسي ومتاح للمدير', (tester) async {
    final teacherApi = _GradeEntryStub();
    await _pumpPage(tester, teacherApi, 'instructor');

    expect(
      tester
          .widget<FilledButton>(find.byKey(const Key('publishGradesButton')))
          .onPressed,
      isNull,
    );
    expect(find.text('النشر يتطلب موافقة مدير الكلية'), findsOneWidget);

    final adminApi = _GradeEntryStub();
    await _pumpPage(tester, adminApi, 'college_admin');

    final publishButton = tester.widget<FilledButton>(
      find.byKey(const Key('publishGradesButton')),
    );
    expect(publishButton.onPressed, isNotNull);
  });

  testWidgets('التقييم المنشور يُقفل الحقول', (tester) async {
    final api = _GradeEntryStub(published: true);
    await _pumpPage(tester, api, 'instructor');

    expect(find.text('التقييم منشور — لا يمكن تعديل درجاته'), findsOneWidget);
    final field = tester.widget<TextField>(find.byKey(const Key('scoreField-s-1')));
    expect(field.enabled, isFalse);
  });
}
