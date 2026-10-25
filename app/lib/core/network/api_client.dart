import 'package:dio/dio.dart';

/// خطأ موحّد من الخادم أو الشبكة.
///
/// `messageAr` يحمل رسالة الخادم العربية عند وجودها؛ وعند غيابها تعرض الواجهة
/// نصاً من ملفات الترجمة بحسب `code` (قاعدة الخطة: لا نصوص عربية داخل الكود).
class ApiException implements Exception {
  ApiException(this.code, this.messageAr, {this.statusCode});

  final String code;
  final String? messageAr;
  final int? statusCode;

  static ApiException fromDio(DioException error) {
    final data = error.response?.data;
    if (data is Map && data['message_ar'] is String) {
      return ApiException(
        (data['code'] as String?) ?? 'error',
        data['message_ar'] as String,
        statusCode: error.response?.statusCode,
      );
    }
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.connectionError:
        return ApiException('network_unreachable', null);
      default:
        return ApiException('unexpected_error', null,
            statusCode: error.response?.statusCode);
    }
  }

  @override
  String toString() => 'ApiException($code): ${messageAr ?? ''}';
}

/// عميل HTTP موحد.
/// المحاكي على نفس الجهاز: 10.0.2.2؛ والسيرفر الجامعي عبر:
/// `flutter run --dart-define=API_BASE_URL=https://csit.qu.edu.iq`
Dio buildDio() {
  return Dio(
    BaseOptions(
      baseUrl: const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://10.0.2.2:8000',
      ),
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 20),
      headers: {'Accept': 'application/json'},
    ),
  );
}
