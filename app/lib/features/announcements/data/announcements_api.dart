import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

/// إعلان موجّه كما يعرضه `GET /announcements`.
class AnnouncementItem {
  const AnnouncementItem({
    required this.id,
    required this.title,
    required this.body,
    required this.priority,
    required this.pinned,
    required this.isRead,
    this.publishedAt,
  });

  final String id;
  final String title;
  final String body;

  /// normal | high
  final String priority;
  final bool pinned;
  final bool isRead;
  final DateTime? publishedAt;

  bool get isHighPriority => priority == 'high';

  factory AnnouncementItem.fromJson(Map<String, dynamic> json) => AnnouncementItem(
        id: json['announcement_id'] as String,
        title: json['title'] as String? ?? '',
        body: json['body'] as String? ?? '',
        priority: json['priority'] as String? ?? 'normal',
        pinned: json['pinned'] as bool? ?? false,
        isRead: json['is_read'] as bool? ?? false,
        publishedAt: DateTime.tryParse(
          (json['publish_at'] ?? json['created_at'] ?? '') as String,
        ),
      );

  Map<String, dynamic> toJson() => {
        'announcement_id': id,
        'title': title,
        'body': body,
        'priority': priority,
        'pinned': pinned,
        'is_read': isRead,
        'publish_at': publishedAt?.toUtc().toIso8601String(),
      };

  AnnouncementItem copyWith({bool? isRead}) => AnnouncementItem(
        id: id,
        title: title,
        body: body,
        priority: priority,
        pinned: pinned,
        isRead: isRead ?? this.isRead,
        publishedAt: publishedAt,
      );
}

/// نتيجة التحميل مع مؤشر «من الذاكرة» عند تعذر الشبكة.
class AnnouncementsData {
  const AnnouncementsData({
    required this.items,
    this.fetchedAt,
    this.fromCache = false,
  });

  final List<AnnouncementItem> items;
  final DateTime? fetchedAt;
  final bool fromCache;
}

abstract class AnnouncementsCache {
  Future<void> save(List<AnnouncementItem> items, DateTime at);

  Future<({List<AnnouncementItem> items, DateTime at})?> read();
}

class PrefsAnnouncementsCache implements AnnouncementsCache {
  static const _key = 'csit.announcements.cache.v1';

  @override
  Future<void> save(List<AnnouncementItem> items, DateTime at) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _key,
      jsonEncode({
        'saved_at': at.toUtc().toIso8601String(),
        'items': items.map((item) => item.toJson()).toList(),
      }),
    );
  }

  @override
  Future<({List<AnnouncementItem> items, DateTime at})?> read() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) {
      return null;
    }
    try {
      final body = jsonDecode(raw) as Map<String, dynamic>;
      final items = (body['items'] as List<dynamic>)
          .whereType<Map<String, dynamic>>()
          .map(AnnouncementItem.fromJson)
          .toList();
      return (items: items, at: DateTime.parse(body['saved_at'] as String));
    } catch (_) {
      return null;
    }
  }
}

abstract class AnnouncementsApi {
  Future<AnnouncementsData> load();

  Future<void> markRead(String announcementId);
}

class HttpAnnouncementsApi implements AnnouncementsApi {
  HttpAnnouncementsApi({
    required Dio dio,
    required TokenStore store,
    AnnouncementsCache? cache,
  })  : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store),
        _cache = cache ?? PrefsAnnouncementsCache();

  final Dio _dio;
  final AuthedDio _authed;
  final AnnouncementsCache _cache;

  Options _auth(String token) =>
      Options(headers: {'Authorization': 'Bearer $token'});

  @override
  Future<AnnouncementsData> load() async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/announcements',
          options: _auth(token),
        ),
      );
      final items = (response.data?['items'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(AnnouncementItem.fromJson)
          .toList();
      final now = DateTime.now().toUtc();
      await _cache.save(items, now);
      return AnnouncementsData(items: items, fetchedAt: now);
    } on ApiException catch (error) {
      if (error.statusCode == 401 || error.statusCode == 403) {
        rethrow;
      }
      final cached = await _cache.read();
      if (cached == null) {
        rethrow;
      }
      return AnnouncementsData(
        items: cached.items,
        fetchedAt: cached.at,
        fromCache: true,
      );
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
