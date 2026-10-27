import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

class IdentityProfile {
  const IdentityProfile({
    required this.universityId,
    required this.fullName,
    this.department,
    this.stage,
    this.group,
  });

  final String universityId;
  final String fullName;
  final String? department;
  final int? stage;
  final String? group;

  factory IdentityProfile.fromJson(Map<String, dynamic> json) => IdentityProfile(
        universityId: json['university_id'] as String? ?? '',
        fullName: json['full_name_ar'] as String? ?? '',
        department: json['department'] as String?,
        stage: json['stage'] as int?,
        group: json['group'] as String?,
      );
}

/// بطاقة موقّعة قصيرة العمر يعرضها التطبيق كرمز QR.
class IdentityCard {
  const IdentityCard({
    required this.card,
    required this.expiresAt,
    required this.profile,
    this.ttlSeconds = 180,
  });

  final String card;
  final DateTime expiresAt;
  final IdentityProfile profile;
  final int ttlSeconds;

  factory IdentityCard.fromJson(Map<String, dynamic> json) => IdentityCard(
        card: json['card'] as String? ?? '',
        expiresAt: DateTime.tryParse(json['expires_at'] as String? ?? '') ??
            DateTime.now().toUtc(),
        profile: IdentityProfile.fromJson(
          (json['profile'] as Map?)?.cast<String, dynamic>() ?? const {},
        ),
        ttlSeconds: json['ttl_seconds'] as int? ?? 180,
      );
}

class VerifiedStudent {
  const VerifiedStudent({
    required this.universityId,
    required this.fullName,
    this.department,
    this.stage,
    this.group,
    this.studyType,
    required this.expiresAt,
  });

  final String universityId;
  final String fullName;
  final String? department;
  final int? stage;
  final String? group;
  final String? studyType;
  final DateTime expiresAt;

  factory VerifiedStudent.fromJson(Map<String, dynamic> json) {
    final student = (json['student'] as Map?)?.cast<String, dynamic>() ?? const {};
    return VerifiedStudent(
      universityId: student['university_id'] as String? ?? '',
      fullName: student['full_name_ar'] as String? ?? '',
      department: student['department'] as String?,
      stage: student['stage'] as int?,
      group: student['group'] as String?,
      studyType: student['study_type'] as String?,
      expiresAt: DateTime.tryParse(json['expires_at'] as String? ?? '') ??
          DateTime.now().toUtc(),
    );
  }
}

abstract class IdentityApi {
  Future<IdentityCard> myCard();

  Future<VerifiedStudent> verify(String card);
}

class HttpIdentityApi implements IdentityApi {
  HttpIdentityApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final AuthedDio _authed;

  Options _auth(String token) =>
      Options(headers: {'Authorization': 'Bearer $token'});

  @override
  Future<IdentityCard> myCard() async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/me/identity-card',
          options: _auth(token),
        ),
      );
      return IdentityCard.fromJson(response.data ?? const <String, dynamic>{});
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<VerifiedStudent> verify(String card) async {
    try {
      final response = await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/identity/verify',
          data: {'card': card},
          options: _auth(token),
        ),
      );
      return VerifiedStudent.fromJson(response.data ?? const <String, dynamic>{});
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }
}
