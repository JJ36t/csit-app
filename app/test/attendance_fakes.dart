import 'dart:async';

import 'package:flutter/widgets.dart';

import 'package:csit/core/network/api_client.dart';
import 'package:csit/features/attendance/data/attendance_api.dart';
import 'package:csit/features/attendance/data/attendance_scanner.dart';
import 'package:csit/features/attendance/data/location_service.dart';
import 'package:csit/features/auth/data/auth_repository.dart';

/// بدائل في الذاكرة لاختبارات شاشات الحضور — بلا شبكة ولا كاميرا ولا تخزين آمن.

/// مصادقة وهمية: تكفي لإنشاء SessionController وتفعيل/إفراغ الجلسة.
class StubAuthApi implements AuthApi {
  UserProfile? _profile;

  static const defaultProfile = UserProfile(
    universityId: '20240001',
    fullNameAr: 'طالب تجريبي',
    role: 'student',
    mustChangePassword: false,
  );

  @override
  Future<bool> hasSession() async => _profile != null;

  @override
  Future<UserProfile> login({
    required String universityId,
    required String password,
  }) async =>
      _profile ??= defaultProfile;

  @override
  Future<UserProfile> me() async {
    final profile = _profile;
    if (profile == null) {
      throw ApiException('not_authenticated', null, statusCode: 401);
    }
    return profile;
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {}

  @override
  Future<void> logout() async {
    _profile = null;
  }
}

/// ماسح وهمي: تُحقن فيه القيم يدوياً عبر emit بدل الكاميرا.
class FakeScanner implements AttendanceScanner {
  final _codes = StreamController<String>.broadcast();

  /// معاينة ثابتة (الاختبار لا يفتح كاميرا).
  @override
  Widget buildPreview({BoxFit fit = BoxFit.cover}) =>
      const SizedBox(key: Key('scannerPreview'), width: 120, height: 160);

  @override
  Stream<String> get codes => _codes.stream;

  @override
  Future<void> dispose() async {}

  void emit(String code) => _codes.add(code);
}

/// خدمة موقع وهمية: تعيد ما يُضبط لها أو null.
class FakeLocationService implements LocationService {
  FakeLocationService([this.location]);

  ScanLocation? location;
  int calls = 0;

  @override
  Future<ScanLocation?> current({
    Duration timeout = const Duration(seconds: 5),
  }) async {
    calls++;
    return location;
  }
}

/// واجهة حضور وهمية: تسجل الاستدعاءات وتعيد بيانات مُعدّة مسبقاً.
class FakeAttendanceApi implements AttendanceApi {
  FakeAttendanceApi({
    this.scanResult,
    this.scanError,
    List<LiveSessionData>? liveResponses,
    this.liveError,
    this.openError,
    this.closeError,
    this.closeResult,
    List<SessionSummary>? sessions,
    this.sessionsError,
  })  : _liveResponses = liveResponses ?? <LiveSessionData>[],
        _sessions = sessions ?? <SessionSummary>[];

  ScanResult? scanResult;
  ApiException? scanError;

  final List<LiveSessionData> _liveResponses;
  LiveSessionData? _lastLive;
  ApiException? liveError;

  ApiException? openError;
  ApiException? closeError;
  CloseResult? closeResult;

  final List<SessionSummary> _sessions;
  ApiException? sessionsError;

  int scanCalls = 0;
  int liveCalls = 0;
  int openCalls = 0;
  int closeCalls = 0;
  int sessionsCalls = 0;

  String? lastSessionId;
  String? lastToken;
  ScanLocation? lastLocation;

  @override
  Future<ScanResult> scan({
    required String sessionId,
    required String token,
    ScanLocation? location,
  }) async {
    scanCalls++;
    lastSessionId = sessionId;
    lastToken = token;
    lastLocation = location;
    final error = scanError;
    if (error != null) {
      throw error;
    }
    return scanResult ??
        const ScanResult(
          attendanceId: 'att-1',
          status: 'present',
          flagged: false,
          messageAr: 'تم تسجيل حضورك',
        );
  }

  @override
  Future<LiveSessionData> liveSession(String sessionId) async {
    liveCalls++;
    if (_liveResponses.isNotEmpty) {
      _lastLive = _liveResponses.removeAt(0);
    }
    final live = _lastLive;
    if (live != null && liveError == null) {
      return live;
    }
    throw liveError ?? ApiException('unexpected_error', null);
  }

  /// تضيف استجابة لحظية جديدة (لاستخدامها في اختبارات إعادة المحاولة).
  void enqueueLive(LiveSessionData data) => _liveResponses.add(data);

  @override
  Future<void> openSession(String sessionId) async {
    openCalls++;
    final error = openError;
    if (error != null) {
      throw error;
    }
  }

  @override
  Future<CloseResult> closeSession(String sessionId) async {
    closeCalls++;
    final error = closeError;
    if (error != null) {
      throw error;
    }
    return closeResult ?? const CloseResult(absentMarked: 0, counts: {});
  }

  @override
  Future<List<SessionSummary>> mySessions() async {
    sessionsCalls++;
    final error = sessionsError;
    if (error != null) {
      throw error;
    }
    return _sessions;
  }
}
