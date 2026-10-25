import 'package:dio/dio.dart';

import '../storage/token_store.dart';
import 'api_client.dart';

/// إرسال الطلبات الموقّعة برمز الوصول مع تجديد تلقائي واحد عند 401.
///
/// المنطق مشترك بين كل المستودعات (المصادقة، الحضور، الجدول…) كي لا يتكرر:
/// رمز وصول من التخزين الآمن ← عند 401 تجديد واحد ← إعادة محاولة واحدة؛
/// وفشل التجديد يُفرغ الرموز ويرمي `session_expired`.
class AuthedDio {
  AuthedDio({required Dio dio, required TokenStore store})
      : _dio = dio,
        _store = store;

  final Dio _dio;
  final TokenStore _store;

  Future<Response<Map<String, dynamic>>> send(
    Future<Response<Map<String, dynamic>>> Function(String token) call,
  ) async {
    var token = await _store.accessToken;
    if (token == null) {
      throw ApiException('not_authenticated', null, statusCode: 401);
    }
    try {
      return await call(token);
    } on DioException catch (error) {
      if (error.response?.statusCode != 401) {
        throw ApiException.fromDio(error);
      }
      final renewed = await _refresh();
      if (!renewed) {
        await _store.clear();
        throw ApiException('session_expired', null, statusCode: 401);
      }
      token = await _store.accessToken;
      if (token == null) {
        throw ApiException('session_expired', null, statusCode: 401);
      }
      try {
        return await call(token);
      } on DioException catch (retryError) {
        throw ApiException.fromDio(retryError);
      }
    }
  }

  Future<bool> _refresh() async {
    final refreshToken = await _store.refreshToken;
    if (refreshToken == null) {
      return false;
    }
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/api/v1/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      final body = response.data ?? const <String, dynamic>{};
      await _store.saveTokens(
        accessToken: body['access_token'] as String,
        refreshToken: body['refresh_token'] as String,
      );
      return true;
    } on DioException {
      return false;
    }
  }
}
