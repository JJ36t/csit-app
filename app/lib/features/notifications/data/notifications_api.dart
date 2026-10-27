import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

/// إشعار داخل التطبيق من `GET /notifications`.
class AppNotification {
  const AppNotification({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    required this.isRead,
    this.createdAt,
    this.data = const {},
  });

  final String id;
  final String type;
  final String title;
  final String body;
  final bool isRead;
  final DateTime? createdAt;
  final Map<String, dynamic> data;

  factory AppNotification.fromJson(Map<String, dynamic> json) => AppNotification(
        id: json['notification_id'] as String,
        type: json['type'] as String? ?? '',
        title: json['title'] as String? ?? '',
        body: json['body'] as String? ?? '',
        isRead: json['read'] as bool? ?? false,
        createdAt: DateTime.tryParse((json['created_at'] ?? '') as String),
        data: (json['data'] as Map?)?.cast<String, dynamic>() ?? const {},
      );
}

class NotificationsData {
  const NotificationsData({required this.items, required this.unreadCount});

  final List<AppNotification> items;
  final int unreadCount;
}

abstract class NotificationsApi {
  Future<NotificationsData> load();

  Future<void> markRead(String notificationId);

  Future<void> markAllRead();

  /// يسجّل رمز FCM للجهاز المربوط الحالي (يُهمَل بهدوء إن لم يكن الجهاز مربوطاً).
  Future<void> registerFcmToken(String token);
}

class HttpNotificationsApi implements NotificationsApi {
  HttpNotificationsApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _store = store,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final TokenStore _store;
  final AuthedDio _authed;

  Options _auth(String token) =>
      Options(headers: {'Authorization': 'Bearer $token'});

  @override
  Future<NotificationsData> load() async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/notifications',
          options: _auth(token),
        ),
      );
      final body = response.data ?? const <String, dynamic>{};
      return NotificationsData(
        items: (body['items'] as List<dynamic>? ?? [])
            .whereType<Map<String, dynamic>>()
            .map(AppNotification.fromJson)
            .toList(),
        unreadCount: body['unread_count'] as int? ?? 0,
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<void> markRead(String notificationId) async {
    try {
      await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/notifications/$notificationId/read',
          options: _auth(token),
        ),
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<void> markAllRead() async {
    try {
      await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/notifications/read-all',
          options: _auth(token),
        ),
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<void> registerFcmToken(String token) async {
    final deviceId = await _store.deviceId;
    if (deviceId == null) {
      return;
    }
    try {
      await _authed.send(
        (access) => _dio.put<Map<String, dynamic>>(
          '/api/v1/devices/fcm-token',
          data: {'token': token, 'device_id': deviceId},
          options: _auth(access),
        ),
      );
    } on DioException {
      // تسجيل الرمز ليس حرجاً: الفشل لا يمنع استخدام التطبيق
    }
  }
}
