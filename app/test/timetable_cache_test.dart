import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:csit/features/timetable/data/timetable_api.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('الجدول يُحفظ ويُقرأ من الذاكرة المحلية كما هو', () async {
    SharedPreferences.setMockInitialValues({});
    final cache = PrefsTimetableCache();
    final at = DateTime.utc(2026, 10, 26, 7, 30);
    final item = SessionItem(
      sessionId: 's-1',
      offeringId: 'offer-1',
      date: DateTime.utc(2026, 10, 26),
      startsAt: DateTime.utc(2026, 10, 26, 7, 30),
      endsAt: DateTime.utc(2026, 10, 26, 9, 0),
      courseCode: 'CS101',
      courseNameAr: 'مقدمة في علوم الحاسوب',
      kind: 'lab',
      room: 'مختبر 3',
      status: 'scheduled',
    );

    await cache.save([item], at);
    final restored = await cache.read();

    expect(restored, isNotNull);
    expect(restored!.at, at);
    expect(restored.items, hasLength(1));
    expect(restored.items.single.sessionId, 's-1');
    expect(restored.items.single.courseNameAr, 'مقدمة في علوم الحاسوب');
    expect(restored.items.single.room, 'مختبر 3');
    expect(restored.items.single.kind, 'lab');
    expect(restored.items.single.startsAt, DateTime.utc(2026, 10, 26, 7, 30));
  });

  test('الذاكرة الفارغة تعيد null بلا استثناء', () async {
    SharedPreferences.setMockInitialValues({});
    final cache = PrefsTimetableCache();

    expect(await cache.read(), isNull);
  });
}
