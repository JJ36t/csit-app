/// محتوى رمز QR المعروض في قاعة المحاضرة (المرحلة 3 من الخطة).
///
/// الصيغة: `csit:v1:<معرف الجلسة UUID>:<window>.<توقيع HMAC>`
/// ينشئه التدريسي في التطبيق من استجابة `/sessions/{id}/live`
/// (معرّف الجلسة + الرمز المتجدد)، ويفكّه تطبيق الطالب عند المسح
/// ثم يرسل القيمتين إلى `POST /attendance/scan`.
class QrPayload {
  const QrPayload({required this.sessionId, required this.token});

  final String sessionId;
  final String token;

  static const _prefix = 'csit:v1:';

  static final _sessionPattern = RegExp(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    caseSensitive: false,
  );

  /// شكل الرمز المتجدد من الخادم: `<window>.<أول 16 محرفاً من HMAC>`.
  static final _tokenPattern = RegExp(r'^\d+\.[0-9a-f]{16}$');

  String encode() => '$_prefix$sessionId:$token';

  /// يعيد القيم عند صحة الصيغة كاملة، وإلا null — بلا استثناءات.
  static QrPayload? tryParse(String raw) {
    if (!raw.startsWith(_prefix)) {
      return null;
    }
    final body = raw.substring(_prefix.length);
    final separator = body.indexOf(':');
    if (separator <= 0) {
      return null;
    }
    final sessionId = body.substring(0, separator);
    final token = body.substring(separator + 1);
    if (!_sessionPattern.hasMatch(sessionId) ||
        !_tokenPattern.hasMatch(token)) {
      return null;
    }
    return QrPayload(sessionId: sessionId.toLowerCase(), token: token);
  }
}
