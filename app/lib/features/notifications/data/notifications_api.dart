import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

/// إشعار واحد في صندوق الوارد (`GET /notifications`).
class NotificationItem {
  const NotificationItem({
    required this.notificationId,
    required this.type,
    required this.title,
    required this.body,
    required this.isRead,
    this.createdAt,
  });

  final String notificationId;

  /// announcement / attendance / … (يأتي من الخادم كنص حر).
  final String type;
  final String title;
  final String body;
  final bool isRead;
  final DateTime? createdAt;

  NotificationItem copyWith({bool? isRead}) => NotificationItem(
        notificationId: notificationId,
        type: type,
        title: title,
        body: body,
        isRead: isRead ?? this.isRead,
        createdAt: createdAt,
      );

  factory NotificationItem.fromJson(Map<String, dynamic> json) =>
      NotificationItem(
        notificationId: json['notification_id'] as String,
        type: json['type'] as String? ?? 'general',
        title: json['title'] as String? ?? '',
        body: json['body'] as String? ?? '',
        // الخادم يرسل `read`؛ ونقبل `is_read` احتياطاً لكلا الشكلين.
        isRead: (json['read'] ?? json['is_read']) as bool? ?? false,
        createdAt: json['created_at'] is String
            ? DateTime.tryParse(json['created_at'] as String)
            : null,
      );
}

/// صندوق الوارد: العناصر مع عدد غير المقروء كما يعيده الخادم.
class NotificationInbox {
  const NotificationInbox({required this.items, required this.unreadCount});

  final List<NotificationItem> items;
  final int unreadCount;

  factory NotificationInbox.fromJson(Map<String, dynamic> json) =>
      NotificationInbox(
        items: (json['items'] as List<dynamic>? ?? [])
            .whereType<Map<String, dynamic>>()
            .map(NotificationItem.fromJson)
            .toList(),
        unreadCount: json['unread_count'] as int? ?? 0,
      );
}

/// واجهة الإشعارات — تُختبر ببديل في الذاكرة.
abstract class NotificationsApi {
  Future<NotificationInbox> inbox();

  Future<void> markRead(String notificationId);

  Future<void> markAllRead();
}

class HttpNotificationsApi implements NotificationsApi {
  HttpNotificationsApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final AuthedDio _authed;

  Options _auth(String token) =>
      Options(headers: {'Authorization': _bearer(token)});

  @override
  Future<NotificationInbox> inbox() async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/notifications',
          options: _auth(token),
        ),
      );
      return NotificationInbox.fromJson(
        response.data ?? const <String, dynamic>{},
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
}

/// قيمة رأس المصادقة — دالة مستقلة حتى يُبنى الرأس في مكان واحد.
String _bearer(String token) => 'Bearer $token';
