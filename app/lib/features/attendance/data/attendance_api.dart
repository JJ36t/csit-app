import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';
import 'location_service.dart';

/// نتيجة المسح كما تعيدها نقطة `POST /attendance/scan`.
class ScanResult {
  const ScanResult({
    required this.attendanceId,
    required this.status,
    required this.flagged,
    this.flagReason,
    required this.messageAr,
  });

  final String attendanceId;

  /// `present` أو `late`.
  final String status;
  final bool flagged;

  /// مثل `outside_campus:120m` أو `no_location` عند التعليم.
  final String? flagReason;
  final String messageAr;

  factory ScanResult.fromJson(Map<String, dynamic> json) => ScanResult(
        attendanceId: json['attendance_id'] as String,
        status: json['status'] as String,
        flagged: json['flagged'] as bool? ?? false,
        flagReason: json['flag_reason'] as String?,
        messageAr: json['message_ar'] as String? ?? '',
      );
}

/// طالب واحد في قائمة الحاضرين اللحظية.
class LiveStudent {
  const LiveStudent({
    required this.universityId,
    required this.fullNameAr,
    this.status,
    this.flagged = false,
  });

  final String universityId;
  final String fullNameAr;

  /// null = لم يُسجّل بعد، وإلا present/late/absent/excused.
  final String? status;
  final bool flagged;

  factory LiveStudent.fromJson(Map<String, dynamic> json) => LiveStudent(
        universityId: json['university_id'] as String,
        fullNameAr: json['full_name_ar'] as String? ?? '',
        status: json['status'] as String?,
        flagged: json['flagged'] as bool? ?? false,
      );
}

/// رمز QR المتجدد كما في استجابة الجلسة اللحظية.
class LiveQr {
  const LiveQr({required this.token, required this.rotationS, required this.expiresIn});

  final String token;
  final int rotationS;
  final int expiresIn;

  factory LiveQr.fromJson(Map<String, dynamic> json) => LiveQr(
        token: json['token'] as String,
        rotationS: json['rotation_s'] as int? ?? 20,
        expiresIn: json['expires_in'] as int? ?? 20,
      );
}

/// حالة الجلسة اللحظية من `GET /sessions/{id}/live`.
class LiveSessionData {
  const LiveSessionData({
    required this.sessionId,
    required this.status,
    required this.startsAt,
    required this.endsAt,
    this.qr,
    required this.counts,
    required this.students,
  });

  final String sessionId;

  /// scheduled / open / closed / cancelled.
  final String status;
  final DateTime startsAt;
  final DateTime endsAt;

  /// موجود فقط والجلسة مفتوحة.
  final LiveQr? qr;

  /// عدد كل حالة مسجَّلة: present/late/absent/excused.
  final Map<String, int> counts;
  final List<LiveStudent> students;

  bool get isOpen => status == 'open';

  factory LiveSessionData.fromJson(Map<String, dynamic> json) => LiveSessionData(
        sessionId: json['session_id'] as String,
        status: json['status'] as String,
        startsAt: DateTime.parse(json['starts_at'] as String),
        endsAt: DateTime.parse(json['ends_at'] as String),
        qr: json['qr'] == null
            ? null
            : LiveQr.fromJson(json['qr'] as Map<String, dynamic>),
        counts: (json['counts'] as Map<String, dynamic>? ?? {})
            .map((key, value) => MapEntry(key, value as int)),
        students: (json['students'] as List<dynamic>? ?? [])
            .map((row) => LiveStudent.fromJson(row as Map<String, dynamic>))
            .toList(),
      );
}

/// نتيجة إغلاق الجلسة.
class CloseResult {
  const CloseResult({required this.absentMarked, required this.counts});

  final int absentMarked;
  final Map<String, int> counts;

  factory CloseResult.fromJson(Map<String, dynamic> json) => CloseResult(
        absentMarked: json['absent_marked'] as int? ?? 0,
        counts: (json['counts'] as Map<String, dynamic>? ?? {})
            .map((key, value) => MapEntry(key, value as int)),
      );
}

/// حصة من جدول المستخدم (`GET /timetable`) — أساس اختيار التدريسي لجلسته.
class SessionSummary {
  const SessionSummary({
    required this.sessionId,
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

  factory SessionSummary.fromJson(Map<String, dynamic> json) => SessionSummary(
        sessionId: json['session_id'] as String,
        date: DateTime.parse(json['date'] as String),
        startsAt: DateTime.parse(json['starts_at'] as String),
        endsAt: DateTime.parse(json['ends_at'] as String),
        courseCode: json['course_code'] as String? ?? '',
        courseNameAr: json['course_name_ar'] as String? ?? '',
        kind: json['kind'] as String? ?? 'theory',
        room: json['room'] as String?,
        status: json['status'] as String? ?? 'scheduled',
      );
}

/// واجهة الحضور — الواجهات تُختبر ببديل في الذاكرة.
abstract class AttendanceApi {
  /// مسح الطالب: يقرأ device_id من التخزين الآمن (حُفظ عند الدخول).
  Future<ScanResult> scan({
    required String sessionId,
    required String token,
    ScanLocation? location,
  });

  Future<LiveSessionData> liveSession(String sessionId);

  Future<void> openSession(String sessionId);

  Future<CloseResult> closeSession(String sessionId);

  /// حصص المستخدم من الجدول (افتراض الخادم: من اليوم حتى أسبوعين).
  Future<List<SessionSummary>> mySessions();
}

/// تنفيذ الحضور عبر الـAPI بلا أي تعديل على الخادم.
class HttpAttendanceApi implements AttendanceApi {
  HttpAttendanceApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _store = store,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final TokenStore _store;
  final AuthedDio _authed;

  Options _auth(String token) =>
      Options(headers: {'Authorization': 'Bearer $token'});

  @override
  Future<ScanResult> scan({
    required String sessionId,
    required String token,
    ScanLocation? location,
  }) async {
    final deviceId = await _store.deviceId;
    if (deviceId == null) {
      // دخول قديم قبل إضافة حفظ المعرّف — الدخول من جديد يكفي.
      throw ApiException('missing_device_id', null);
    }
    try {
      final response = await _authed.send(
        (auth) => _dio.post<Map<String, dynamic>>(
          '/api/v1/attendance/scan',
          data: {
            'session_id': sessionId,
            'token': token,
            'device_id': deviceId,
            if (location != null) 'location': location.toJson(),
          },
          options: _auth(auth),
        ),
      );
      return ScanResult.fromJson(response.data ?? const <String, dynamic>{});
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<LiveSessionData> liveSession(String sessionId) async {
    try {
      final response = await _authed.send(
        (auth) => _dio.get<Map<String, dynamic>>(
          '/api/v1/sessions/$sessionId/live',
          options: _auth(auth),
        ),
      );
      return LiveSessionData.fromJson(response.data ?? const <String, dynamic>{});
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<void> openSession(String sessionId) async {
    try {
      await _authed.send(
        (auth) => _dio.post<Map<String, dynamic>>(
          '/api/v1/sessions/$sessionId/open',
          options: _auth(auth),
        ),
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<CloseResult> closeSession(String sessionId) async {
    try {
      final response = await _authed.send(
        (auth) => _dio.post<Map<String, dynamic>>(
          '/api/v1/sessions/$sessionId/close',
          options: _auth(auth),
        ),
      );
      return CloseResult.fromJson(response.data ?? const <String, dynamic>{});
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<List<SessionSummary>> mySessions() async {
    try {
      final response = await _authed.send(
        (auth) => _dio.get<Map<String, dynamic>>(
          '/api/v1/timetable',
          options: _auth(auth),
        ),
      );
      final items =
          (response.data?['items'] as List<dynamic>? ?? <dynamic>[])
              .whereType<Map<String, dynamic>>()
              .map(SessionSummary.fromJson)
              .toList();
      return items;
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }
}
