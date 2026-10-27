import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';
import '../../../core/utils/date_utils.dart';

/// مرفق عذر (صورة/PDF) مع رابط تنزيل موقّع قصير العمر.
class ExcuseAttachment {
  const ExcuseAttachment({required this.name, required this.downloadUrl, this.size});

  final String name;
  final String downloadUrl;
  final int? size;

  factory ExcuseAttachment.fromJson(Map<String, dynamic> json) => ExcuseAttachment(
        name: json['name'] as String? ?? '',
        downloadUrl: json['download_url'] as String? ?? '',
        size: json['size'] as int?,
      );
}

class ExcuseItem {
  const ExcuseItem({
    required this.id,
    required this.sessionId,
    required this.sessionDate,
    required this.courseCode,
    required this.courseName,
    required this.status,
    required this.reason,
    this.reviewNote,
    this.studentName,
    this.attachment,
    this.createdAt,
  });

  final String id;
  final String sessionId;
  final DateTime sessionDate;
  final String courseCode;
  final String courseName;

  /// pending | approved | rejected
  final String status;
  final String reason;
  final String? reviewNote;
  final String? studentName;
  final ExcuseAttachment? attachment;
  final DateTime? createdAt;

  bool get isPending => status == 'pending';

  factory ExcuseItem.fromJson(Map<String, dynamic> json) => ExcuseItem(
        id: json['excuse_id'] as String,
        sessionId: json['session_id'] as String? ?? '',
        sessionDate: DateTime.tryParse(json['session_date'] as String? ?? '') ??
            DateTime.now(),
        courseCode: json['course_code'] as String? ?? '',
        courseName: json['course_name_ar'] as String? ?? '',
        status: json['status'] as String? ?? 'pending',
        reason: json['reason'] as String? ?? '',
        reviewNote: json['review_note'] as String?,
        studentName: json['student_name_ar'] as String?,
        attachment: json['attachment'] is Map<String, dynamic>
            ? ExcuseAttachment.fromJson(json['attachment'] as Map<String, dynamic>)
            : null,
        createdAt: DateTime.tryParse(json['created_at'] as String? ?? ''),
      );
}

/// محاضرة مؤهلة لرفع عذر (من الجدول خلال آخر 14 يوماً).
class ExcuseSession {
  const ExcuseSession({
    required this.sessionId,
    required this.courseName,
    required this.date,
  });

  final String sessionId;
  final String courseName;
  final DateTime date;
}

abstract class ExcusesApi {
  Future<List<ExcuseItem>> myExcuses();

  Future<List<ExcuseSession>> eligibleSessions();

  Future<ExcuseItem> submit({
    required String sessionId,
    required String reason,
    String? filePath,
    String? fileName,
  });

  Future<void> withdraw(String excuseId);

  Future<({List<ExcuseItem> items, int pendingTotal})> reviewQueue();

  Future<void> review(String excuseId, {required bool approve, String? note});
}

class HttpExcusesApi implements ExcusesApi {
  HttpExcusesApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final AuthedDio _authed;

  Options _auth(String token) =>
      Options(headers: {'Authorization': 'Bearer $token'});

  @override
  Future<List<ExcuseItem>> myExcuses() async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/excuses',
          options: _auth(token),
        ),
      );
      return (response.data?['items'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(ExcuseItem.fromJson)
          .toList();
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<List<ExcuseSession>> eligibleSessions() async {
    final now = DateTime.now().toUtc();
    final from = now.subtract(const Duration(days: 14));
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/timetable',
          queryParameters: {'from': _date(from), 'to': _date(now)},
          options: _auth(token),
        ),
      );
      final sessions = <ExcuseSession>[];
      for (final row in (response.data?['items'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()) {
        final date = DateTime.tryParse(row['date'] as String? ?? '');
        final status = row['status'] as String? ?? '';
        if (date == null || status == 'cancelled') {
          continue;
        }
        final baghdadToday = toBaghdad(now);
        if (DateTime(date.year, date.month, date.day)
            .isAfter(DateTime(baghdadToday.year, baghdadToday.month, baghdadToday.day))) {
          continue;
        }
        sessions.add(
          ExcuseSession(
            sessionId: row['session_id'] as String,
            courseName: row['course_name_ar'] as String? ?? '',
            date: date,
          ),
        );
      }
      sessions.sort((a, b) => b.date.compareTo(a.date));
      return sessions;
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<ExcuseItem> submit({
    required String sessionId,
    required String reason,
    String? filePath,
    String? fileName,
  }) async {
    try {
      final form = FormData.fromMap({
        'session_id': sessionId,
        'reason': reason,
        if (filePath != null)
          'file': await MultipartFile.fromFile(
            filePath,
            filename: fileName ?? 'excuse',
          ),
      });
      final response = await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/excuses',
          data: form,
          options: _auth(token),
        ),
      );
      return ExcuseItem.fromJson(response.data ?? const <String, dynamic>{});
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<void> withdraw(String excuseId) async {
    try {
      await _authed.send(
        (token) => _dio.delete<Map<String, dynamic>>(
          '/api/v1/excuses/$excuseId',
          options: _auth(token),
        ),
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<({List<ExcuseItem> items, int pendingTotal})> reviewQueue() async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/admin/excuses',
          options: _auth(token),
        ),
      );
      final body = response.data ?? const <String, dynamic>{};
      return (
        items: (body['items'] as List<dynamic>? ?? [])
            .whereType<Map<String, dynamic>>()
            .map(ExcuseItem.fromJson)
            .toList(),
        pendingTotal: body['pending_total'] as int? ?? 0,
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<void> review(
    String excuseId, {
    required bool approve,
    String? note,
  }) async {
    try {
      await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/admin/excuses/$excuseId/review',
          data: {
            'status': approve ? 'approved' : 'rejected',
            if (note != null && note.isNotEmpty) 'note': note,
          },
          options: _auth(token),
        ),
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  static String _date(DateTime moment) {
    final local = toBaghdad(moment);
    final y = local.year.toString().padLeft(4, '0');
    final m = local.month.toString().padLeft(2, '0');
    final d = local.day.toString().padLeft(2, '0');
    return '$y-$m-$d';
  }
}
