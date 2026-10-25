import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

/// تجريد الماسح — يسمح باختبار شاشة المسح ببديل في الذاكرة بلا كاميرا.
abstract class AttendanceScanner {
  /// قيم QR المفكوكة (بلا تكرار متتالٍ للقيمة نفسها).
  Stream<String> get codes;

  /// معاينة الكاميرا (أو بديل ثابت في الاختبارات).
  Widget buildPreview({BoxFit fit = BoxFit.cover});

  Future<void> dispose();
}

/// ماسح QR بالكاميرا الخلفية عبر mobile_scanner.
class MobileScannerAttendanceScanner implements AttendanceScanner {
  MobileScannerAttendanceScanner()
      : _controller = MobileScannerController(
          detectionSpeed: DetectionSpeed.noDuplicates,
          formats: const [BarcodeFormat.qrCode],
        );

  final MobileScannerController _controller;

  @override
  Stream<String> get codes => _controller.barcodes
      .map((capture) => capture.barcodes
          .map((barcode) => barcode.rawValue)
          .whereType<String>()
          .where((value) => value.isNotEmpty))
      .where((values) => values.isNotEmpty)
      .map((values) => values.first);

  @override
  Widget buildPreview({BoxFit fit = BoxFit.cover}) =>
      MobileScanner(controller: _controller, fit: fit);

  @override
  Future<void> dispose() => _controller.dispose();
}
