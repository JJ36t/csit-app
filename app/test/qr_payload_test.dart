import 'package:flutter_test/flutter_test.dart';

import 'package:csit/features/attendance/data/qr_payload.dart';

const _sessionId = '3fa85f64-5717-4562-b3fc-2c963f66afa6';
const _token = '1761234567.abcdef0123456789';

void main() {
  test('الترميز ثم التفكيك يعيد القيم نفسها', () {
    const payload = QrPayload(sessionId: _sessionId, token: _token);
    final parsed = QrPayload.tryParse(payload.encode());

    expect(parsed, isNotNull);
    expect(parsed!.sessionId, _sessionId);
    expect(parsed.token, _token);
  });

  test('المحتوى التالف يُرفض بلا استثناء', () {
    expect(QrPayload.tryParse(''), isNull);
    expect(QrPayload.tryParse('hello world'), isNull);
    expect(QrPayload.tryParse('csit:v1:not-a-uuid:$_token'), isNull);
    expect(QrPayload.tryParse('csit:v1:$_sessionId:bad-token'), isNull);
    expect(QrPayload.tryParse('csit:v2:$_sessionId:$_token'), isNull);
    expect(QrPayload.tryParse('csit:v1:$_sessionId'), isNull);
  });

  test('المعرّف بأحرف كبيرة يُقبل ويُوحَّد إلى صغيرة', () {
    final parsed = QrPayload.tryParse(
      'csit:v1:3FA85F64-5717-4562-B3FC-2C963F66AFA6:$_token',
    );
    expect(parsed?.sessionId, _sessionId);
  });
}
