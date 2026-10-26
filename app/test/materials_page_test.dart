import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/core/network/api_client.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/features/materials/data/materials_api.dart';
import 'package:csit/features/materials/presentation/materials_page.dart';
import 'package:csit/l10n/app_localizations.dart';

import 'academic_fakes.dart';
import 'attendance_fakes.dart';

const _offering = OfferingSummary(
  offeringId: 'offer-1',
  courseCode: 'CS101',
  courseNameAr: 'مقدمة في علوم الحاسوب',
  kind: 'theory',
  stage: 1,
  groupName: 'A',
  studyType: 'morning',
  instructorNameAr: 'د. أحمد التدريسي',
);

MaterialItem _pdf({String? downloadUrl = '/api/v1/files/f-1/download?expires=1&sig=abc'}) =>
    MaterialItem(
      materialId: 'm-1',
      title: 'محاضرة 1 — مقدمة',
      kind: 'pdf',
      weekNo: 1,
      isPublished: true,
      downloadUrl: downloadUrl,
      fileName: 'lecture.pdf',
      fileSize: 2048,
    );

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('ar'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    );

Future<void> _pump(WidgetTester tester, FakeMaterialsApi api, FakeLinkOpener opener) async {
  tester.view.physicalSize = const Size(1170, 3300);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(_wrap(MaterialsPage(
    api: api,
    session: SessionController(StubAuthApi()),
    opener: opener,
  )));
}

void main() {
  testWidgets('تعرض المواد الدراسية ثم ملفات المادة المختارة', (tester) async {
    final api = FakeMaterialsApi(
      offerings: const [_offering],
      materials: {
        'offer-1': [_pdf()],
      },
    );
    final opener = FakeLinkOpener();
    await _pump(tester, api, opener);
    await tester.pumpAndSettle();

    expect(find.text('مقدمة في علوم الحاسوب'), findsOneWidget);
    expect(find.textContaining('CS101'), findsOneWidget);

    await tester.tap(find.byKey(const Key('offeringTile-offer-1')));
    await tester.pumpAndSettle();

    expect(find.text('محاضرة 1 — مقدمة'), findsOneWidget);
    expect(find.textContaining('الأسبوع 1'), findsOneWidget);
    expect(find.byKey(const Key('materialOpen-m-1')), findsOneWidget);
  });

  testWidgets('زر التنزيل يفتح الرابط الموقّع كاملاً', (tester) async {
    final api = FakeMaterialsApi(
      offerings: const [_offering],
      materials: {
        'offer-1': [_pdf()],
      },
    );
    final opener = FakeLinkOpener();
    await _pump(tester, api, opener);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('offeringTile-offer-1')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('materialOpen-m-1')));
    await tester.pumpAndSettle();

    expect(opener.opened, hasLength(1));
    expect(
      opener.opened.single.toString(),
      'http://10.0.2.2:8000/api/v1/files/f-1/download?expires=1&sig=abc',
    );
  });

  testWidgets('فشل فتح الرابط يعرض تنبيهاً', (tester) async {
    final api = FakeMaterialsApi(
      offerings: const [_offering],
      materials: {
        'offer-1': [_pdf()],
      },
    );
    final opener = FakeLinkOpener(result: false);
    await _pump(tester, api, opener);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('offeringTile-offer-1')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('materialOpen-m-1')));
    await tester.pumpAndSettle();

    expect(find.text('تعذر فتح الرابط؛ حاول مجدداً'), findsOneWidget);
  });

  testWidgets('لا مواد منشورة تُظهر رسالة الفراغ', (tester) async {
    final api = FakeMaterialsApi(
      offerings: const [_offering],
      materials: {'offer-1': const []},
    );
    await _pump(tester, api, FakeLinkOpener());
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('offeringTile-offer-1')));
    await tester.pumpAndSettle();

    expect(find.text('لا مواد منشورة بعد'), findsOneWidget);
  });

  testWidgets('فشل تحميل قائمة المواد يعرض إعادة المحاولة', (tester) async {
    final api = FakeMaterialsApi(
      offerings: const [_offering],
      offeringsError: null,
      materialsError: ApiException('network_unreachable', null),
      materials: {'offer-1': [_pdf()]},
    );
    await _pump(tester, api, FakeLinkOpener());
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('offeringTile-offer-1')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('offeringMaterialsRetry')), findsOneWidget);

    api.materialsError = null;
    await tester.tap(find.byKey(const Key('offeringMaterialsRetry')));
    await tester.pumpAndSettle();

    expect(find.text('محاضرة 1 — مقدمة'), findsOneWidget);
  });
}
