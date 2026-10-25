import 'dart:io' show Platform;

import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

/// ملف المستخدم كما يعيده الخادم.
class UserProfile {
  const UserProfile({
    required this.universityId,
    required this.fullNameAr,
    required this.role,
    required this.mustChangePassword,
    this.departmentName,
    this.stage,
    this.groupName,
  });

  final String universityId;
  final String fullNameAr;
  final String role;
  final bool mustChangePassword;
  final String? departmentName;
  final int? stage;
  final String? groupName;

  bool get isStudent => role == 'student';

  bool get isInstructor => role == 'instructor';

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    final student = json['student'] as Map<String, dynamic>?;
    final department = student?['department'] as Map<String, dynamic>?;
    return UserProfile(
      universityId: json['university_id'] as String? ?? '',
      fullNameAr: json['full_name_ar'] as String? ?? '',
      role: json['role'] as String? ?? 'student',
      mustChangePassword: json['must_change_password'] as bool? ?? false,
      departmentName: department?['name_ar'] as String?,
      stage: student?['stage'] as int?,
      groupName: student?['group_name'] as String?,
    );
  }
}

/// واجهة المصادقة — يعتمد عليها الواجهة كي تُختبر ببديل في الذاكرة.
abstract class AuthApi {
  Future<UserProfile> login({
    required String universityId,
    required String password,
  });

  Future<UserProfile> me();

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  });

  Future<void> logout();

  Future<bool> hasSession();
}

/// تنفيذ المصادقة عبر الـAPI: دخول، تجديد تلقائي عند 401، خروج.
class HttpAuthApi implements AuthApi {
  HttpAuthApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _store = store,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final TokenStore _store;
  final AuthedDio _authed;

  @override
  Future<bool> hasSession() async => (await _store.refreshToken) != null;

  @override
  Future<UserProfile> login({
    required String universityId,
    required String password,
  }) async {
    final fingerprint = await _store.deviceFingerprint();
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/api/v1/auth/login',
        data: {
          'university_id': universityId.trim(),
          'password': password,
          'device': {
            'fingerprint': fingerprint,
            'model': Platform.operatingSystem,
          },
        },
      );
      final body = response.data ?? const <String, dynamic>{};
      await _store.saveTokens(
        accessToken: body['access_token'] as String,
        refreshToken: body['refresh_token'] as String,
      );
      // معرّف الجهاز يلزم شاشة المسح — يُحفظ مع الرموز عند كل دخول.
      final deviceId = body['device_id'];
      if (deviceId is String && deviceId.isNotEmpty) {
        await _store.saveDeviceId(deviceId);
      }
      return UserProfile.fromJson(body['user'] as Map<String, dynamic>);
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<UserProfile> me() async {
    final response = await _authed.send(
      (token) => _dio.get<Map<String, dynamic>>(
        '/api/v1/auth/me',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      ),
    );
    return UserProfile.fromJson(response.data ?? const <String, dynamic>{});
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    await _authed.send(
      (token) => _dio.post<Map<String, dynamic>>(
        '/api/v1/auth/change-password',
        data: {
          'current_password': currentPassword,
          'new_password': newPassword,
        },
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      ),
    );
    // الخادم يُلغي كل الجلسات بعد التغيير — يُطلب الدخول من جديد.
    await _store.clear();
  }

  @override
  Future<void> logout() async {
    final token = await _store.accessToken;
    if (token != null) {
      try {
        await _dio.post<Map<String, dynamic>>(
          '/api/v1/auth/logout',
          options: Options(headers: {'Authorization': 'Bearer $token'}),
        );
      } on DioException {
        // لا يعطّل الخروجَ فشلُ الشبكة — تُمسح الرموز محلياً على أي حال.
      }
    }
    await _store.clear();
  }
}
