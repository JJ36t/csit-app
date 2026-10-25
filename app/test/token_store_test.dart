import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:csit/core/storage/token_store.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  test('معرّف الجهاز يُحفظ ويُقرأ ويُمسح مع clear', () async {
    final store = TokenStore();
    expect(await store.deviceId, isNull);

    await store.saveDeviceId('11111111-2222-3333-4444-555555555555');
    expect(await store.deviceId, '11111111-2222-3333-4444-555555555555');

    await store.clear();
    expect(await store.deviceId, isNull);
  });

  test('بصمة الجهاز تُولَّد مرة وتبقى ثابتة', () async {
    final store = TokenStore();
    final first = await store.deviceFingerprint();
    final second = await store.deviceFingerprint();

    expect(first, second);
    expect(first.startsWith('dev-'), isTrue);
    expect(first.length, 36); // "dev-" + 32 محرفاً ست عشرياً
  });
}
