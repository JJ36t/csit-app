import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

class TwoFactorStatus {
  const TwoFactorStatus({
    required this.enabled,
    required this.available,
    this.confirmedAt,
  });

  final bool enabled;
  final bool available;
  final DateTime? confirmedAt;
}

class TwoFactorSetup {
  const TwoFactorSetup({required this.secret, required this.otpauthUri});

  final String secret;
  final String otpauthUri;
}

abstract class TwoFactorApi {
  Future<TwoFactorStatus> status();

  Future<TwoFactorSetup> setup();

  Future<void> enable(String code);

  Future<void> disable(String password);
}

class HttpTwoFactorApi implements TwoFactorApi {
  HttpTwoFactorApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final AuthedDio _authed;

  Options _auth(String token) =>
      Options(headers: {'Authorization': 'Bearer $token'});

  @override
  Future<TwoFactorStatus> status() async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/auth/2fa/status',
          options: _auth(token),
        ),
      );
      final body = response.data ?? const <String, dynamic>{};
      return TwoFactorStatus(
        enabled: body['enabled'] as bool? ?? false,
        available: body['available'] as bool? ?? false,
        confirmedAt: DateTime.tryParse(body['confirmed_at'] as String? ?? ''),
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<TwoFactorSetup> setup() async {
    try {
      final response = await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/auth/2fa/setup',
          options: _auth(token),
        ),
      );
      final body = response.data ?? const <String, dynamic>{};
      return TwoFactorSetup(
        secret: body['secret'] as String? ?? '',
        otpauthUri: body['otpauth_uri'] as String? ?? '',
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<void> enable(String code) async {
    try {
      await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/auth/2fa/enable',
          data: {'code': code},
          options: _auth(token),
        ),
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<void> disable(String password) async {
    try {
      await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/auth/2fa/disable',
          data: {'password': password},
          options: _auth(token),
        ),
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }
}
