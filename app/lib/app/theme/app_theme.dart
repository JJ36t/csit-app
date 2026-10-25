import 'package:flutter/material.dart';

/// سمة التطبيق — الألوان مؤقتة.
/// TODO(design): ألوان الكلية الرسمية + خط Cairo/IBM Plex Sans Arabic
/// مع تباين لا يقل عن 4.5:1 والوضع الليلي في مرحلة التوسعة (القسم 12).
class AppTheme {
  AppTheme._();

  static const primary = Color(0xFF1F4E79);

  static ThemeData get light => ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: primary),
        scaffoldBackgroundColor: const Color(0xFFF7F9FC),
      );
}
