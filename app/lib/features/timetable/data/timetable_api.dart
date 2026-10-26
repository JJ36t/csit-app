import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

/// حصة في جدول المستخدم (`GET /timetable`).
class SessionItem {
  const SessionItem({
    required this.sessionId,
    required this.offeringId,
    required this.date,
    required this.startsAt,
    required this.endsAt,
    required this.courseCode,
    required this.courseNameAr,
    required this.kind,
    this.room,
    required this.status,
  });

  final String sessionId;
  final String offeringId;
  final DateTime date;
  final DateTime startsAt;
  final DateTime endsAt;
  final String courseCode;
  final String courseNameAr;

  /// theory / lab.
  final String kind;
  final String? room;

  /// scheduled / open / closed / cancelled.
  final String status;

  factory SessionItem.fromJson(Map<String, dynamic> json) => SessionItem(
        sessionId: json['session_id'] as String,
        offeringId: json['offering_id'] as String? ?? '',
        date: DateTime.parse(json['date'] as String),
        startsAt: DateTime.parse(json['starts_at'] as String),
        endsAt: DateTime.parse(json['ends_at'] as String),
        courseCode: json['course_code'] as String? ?? '',
        courseNameAr: json['course_name_ar'] as String? ?? '',
        kind: json['kind'] as String? ?? 'theory',
        room: json['room'] as String?,
        status: json['status'] as String? ?? 'scheduled',
      );

  /// للتخزين المحلي (نفس شكل الخادم).
  Map<String, dynamic> toJson() => {
        'session_id': sessionId,
        'offering_id': offeringId,
        'date': date.toIso8601String(),
        'starts_at': startsAt.toIso8601String(),
        'ends_at': endsAt.toIso8601String(),
        'course_code': courseCode,
        'course_name_ar': courseNameAr,
        'kind': kind,
        'room': room,
        'status': status,
      };
}

/// تغيير مؤرخ على الجدول (إلغاء/نقل/إضافة).
class TimetableChange {
  const TimetableChange({
    required this.changeId,
    required this.date,
    required this.type,
    required this.courseNameAr,
    this.newStart,
    this.reason,
  });

  final String changeId;
  final DateTime date;

  /// cancel / move / extra.
  final String type;
  final String courseNameAr;
  final DateTime? newStart;
  final String? reason;

  factory TimetableChange.fromJson(Map<String, dynamic> json) => TimetableChange(
        changeId: json['change_id'] as String,
        date: DateTime.parse(json['date'] as String),
        type: json['type'] as String? ?? 'move',
        courseNameAr: json['course_name_ar'] as String? ?? '',
        newStart: json['new_start'] == null
            ? null
            : DateTime.parse(json['new_start'] as String),
        reason: json['reason'] as String?,
      );
}

/// نتيجة تحميل الجدول — مع مؤشر «من الذاكرة» عند تعذر الشبكة.
class TimetableData {
  const TimetableData({
    required this.sessions,
    required this.changes,
    this.fetchedAt,
    this.fromCache = false,
  });

  final List<SessionItem> sessions;
  final List<TimetableChange> changes;
  final DateTime? fetchedAt;
  final bool fromCache;
}

/// تخزين محلي بسيط للجدول (قراءة بلا إنترنت).
abstract class TimetableCache {
  Future<void> save(List<SessionItem> items, DateTime at);

  Future<({List<SessionItem> items, DateTime at})?> read();
}

class PrefsTimetableCache implements TimetableCache {
  static const _key = 'csit.timetable.cache.v1';

  @override
  Future<void> save(List<SessionItem> items, DateTime at) async {
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
  Future<({List<SessionItem> items, DateTime at})?> read() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) {
      return null;
    }
    try {
      final body = jsonDecode(raw) as Map<String, dynamic>;
      final items = (body['items'] as List<dynamic>)
          .whereType<Map<String, dynamic>>()
          .map(SessionItem.fromJson)
          .toList();
      return (items: items, at: DateTime.parse(body['saved_at'] as String));
    } catch (_) {
      return null;
    }
  }
}

/// واجهة الجدول — تُختبر ببديل في الذاكرة.
abstract class TimetableApi {
  Future<TimetableData> load({DateTime? from, DateTime? to});
}

class HttpTimetableApi implements TimetableApi {
  HttpTimetableApi({
    required Dio dio,
    required TokenStore store,
    TimetableCache? cache,
  })  : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store),
        _cache = cache ?? PrefsTimetableCache();

  final Dio _dio;
  final AuthedDio _authed;
  final TimetableCache _cache;

  Options _auth(String token) =>
      Options(headers: {'Authorization': 'Bearer $token'});

  @override
  Future<TimetableData> load({DateTime? from, DateTime? to}) async {
    try {
      final responses = await Future.wait([
        _authed.send((token) => _dio.get<Map<String, dynamic>>(
              '/api/v1/timetable',
              queryParameters: {
                if (from != null) 'from': _date(from),
                if (to != null) 'to': _date(to),
              },
              options: _auth(token),
            )),
        _authed.send((token) => _dio.get<Map<String, dynamic>>(
              '/api/v1/timetable/changes',
              queryParameters: {
                if (from != null) 'from': _date(from),
                if (to != null) 'to': _date(to),
              },
              options: _auth(token),
            )),
      ]);
      final sessions = (responses[0].data?['items'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(SessionItem.fromJson)
          .toList();
      final changes = (responses[1].data?['items'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(TimetableChange.fromJson)
          .toList();
      final now = DateTime.now().toUtc();
      await _cache.save(sessions, now);
      return TimetableData(sessions: sessions, changes: changes, fetchedAt: now);
    } on ApiException catch (error) {
      // لا نخدم ذاكرة عند انتهاء الجلسة أو رفض الصلاحية.
      if (error.statusCode == 401 || error.statusCode == 403) {
        rethrow;
      }
      final cached = await _cache.read();
      if (cached == null) {
        rethrow;
      }
      return TimetableData(
        sessions: cached.items,
        changes: const [],
        fetchedAt: cached.at,
        fromCache: true,
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  String _date(DateTime moment) {
    final y = moment.year.toString().padLeft(4, '0');
    final m = moment.month.toString().padLeft(2, '0');
    final d = moment.day.toString().padLeft(2, '0');
    return '$y-$m-$d';
  }
}
