import 'dart:math';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// تخزين آمن للرموز وبصمة الجهاز (Keystore على أندرويد).
///
/// لا يُستدعى في اختبارات الواجهة — الاختبارات تستخدم بديلاً في الذاكرة.
class TokenStore {
  TokenStore([FlutterSecureStorage? storage])
      : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  static const _accessKey = 'csit.access_token';
  static const _refreshKey = 'csit.refresh_token';
  static const _deviceKey = 'csit.device_fingerprint';
  static const _deviceIdKey = 'csit.device_id';

  Future<String?> get accessToken => _storage.read(key: _accessKey);

  Future<String?> get refreshToken => _storage.read(key: _refreshKey);

  /// معرّف الجهاز المربوط كما أعاده الخادم عند الدخول — يلزم لنقطة المسح.
  Future<String?> get deviceId => _storage.read(key: _deviceIdKey);

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(key: _accessKey, value: accessToken);
    await _storage.write(key: _refreshKey, value: refreshToken);
  }

  /// يُحفظ عند الدخول فقط؛ إعادة الضبط تفرض دخولاً جديداً يعيده.
  Future<void> saveDeviceId(String deviceId) async {
    await _storage.write(key: _deviceIdKey, value: deviceId);
  }

  Future<void> clear() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
    await _storage.delete(key: _deviceIdKey);
  }

  /// بصمة ثابتة لهذا التثبيت: تُولَّد مرة وتُحفظ، ويُربط بها الجهاز في الخادم.
  Future<String> deviceFingerprint() async {
    final existing = await _storage.read(key: _deviceKey);
    if (existing != null && existing.length >= 16) {
      return existing;
    }
    final random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));
    final fingerprint =
        'dev-${bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join()}';
    await _storage.write(key: _deviceKey, value: fingerprint);
    return fingerprint;
  }
}
