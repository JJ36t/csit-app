import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

/// إعلان موجّه للمستخدم كما يعيده `GET /announcements` (الخلاصة الموجّهة).
class AnnouncementItem {
  const AnnouncementItem({
    required this.announcementId,
    required this.scope,
    required this.title,
    required this.body,
    required this.priority,
    required this.pinned,
    required this.isRead,
    this.publishAt,
    this.createdAt,
  });

  final String announcementId;

  /// college / department / stage / group / offering.
  final String scope;
  final String title;
  final String body;

  /// normal / high.
  final String priority;
  final bool pinned;
  final bool isRead;
  final DateTime? publishAt;
  final DateTime? createdAt;

  /// الأولوية العالية تُبرز بشريحة «عاجل» في القائمة.
  bool get isHighPriority => priority == 'high';

  /// لحظة العرض: النشر إن وُجد وإلا الإنشاء.
  DateTime? get publishedAt => publishAt ?? createdAt;

  AnnouncementItem copyWith({bool? isRead}) => AnnouncementItem(
        announcementId: announcementId,
        scope: scope,
        title: title,
        body: body,
        priority: priority,
        pinned: pinned,
        isRead: isRead ?? this.isRead,
        publishAt: publishAt,
        createdAt: createdAt,
      );

  factory AnnouncementItem.fromJson(Map<String, dynamic> json) =>
      AnnouncementItem(
        announcementId: json['announcement_id'] as String,
        scope: json['scope'] as String? ?? 'college',
        title: json['title'] as String? ?? '',
        body: json['body'] as String? ?? '',
        priority: json['priority'] as String? ?? 'normal',
        pinned: json['pinned'] as bool? ?? false,
        isRead: json['is_read'] as bool? ?? false,
        publishAt: _parseDate(json['publish_at']),
        createdAt: _parseDate(json['created_at']),
      );
}

DateTime? _parseDate(Object? value) =>
    value is String ? DateTime.tryParse(value) : null;

/// واجهة الإعلانات — تُختبر ببديل في الذاكرة.
abstract class AnnouncementsApi {
  Future<List<AnnouncementItem>> feed();

  Future<void> markRead(String announcementId);
}

class HttpAnnouncementsApi implements AnnouncementsApi {
  HttpAnnouncementsApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final AuthedDio _authed;

  Options _auth(String token) =>
      Options(headers: {'Authorization': _bearer(token)});

  @override
  Future<List<AnnouncementItem>> feed() async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/announcements',
          options: _auth(token),
        ),
      );
      return (response.data?['items'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(AnnouncementItem.fromJson)
          .toList();
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<void> markRead(String announcementId) async {
    try {
      await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/announcements/$announcementId/read',
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

