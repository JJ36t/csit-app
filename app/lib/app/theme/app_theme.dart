import 'package:flutter/material.dart';

/// سمة التطبيق — مأخوذة حرفياً من رموز التصميم في `design/screens.html`:
/// primary `#1F4E79` · secondary `#2E74B5` · خلفية `#F7F9FC` · حدود `#DCE4EE`
/// · خطأ `#B3261E` · نجاح `#1B7A55` · نصف قطر 12.
///
/// الخط: خط النظام (Tahoma/Segoe UI على ويندوز، Noto على أندرويد) كما في
/// النموذج — لا خطوط مضمَّنة، فلا حاجة لأصول إضافية ولا تحميل وقت تشغيل.
class AppTheme {
  AppTheme._();

  static const primary = Color(0xFF1F4E79);
  static const primaryDeep = Color(0xFF173D5E);
  static const secondary = Color(0xFF2E74B5);
  static const bgLight = Color(0xFFF7F9FC);
  static const borderLight = Color(0xFFDCE4EE);
  static const textMain = Color(0xFF212121);
  static const muted = Color(0xFF5B6875);
  static const danger = Color(0xFFB3261E);
  static const success = Color(0xFF1B7A55);
  static const radius = 12.0;

  static ThemeData get light => _build(Brightness.light);

  static ThemeData get dark => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final isLight = brightness == Brightness.light;
    final base = ColorScheme.fromSeed(seedColor: primary, brightness: brightness);
    final scheme = base.copyWith(
      primary: isLight ? primary : base.primary,
      secondary: isLight ? secondary : base.secondary,
      error: danger,
      surface: isLight ? Colors.white : const Color(0xFF151B22),
      outlineVariant: isLight ? borderLight : const Color(0xFF2C3A47),
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: isLight ? bgLight : const Color(0xFF0F1418),
      appBarTheme: AppBarTheme(
        backgroundColor: scheme.surface,
        foregroundColor: isLight ? textMain : scheme.onSurface,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w700,
          color: isLight ? textMain : scheme.onSurface,
        ),
        shape: Border(
          bottom: BorderSide(
            color: isLight ? borderLight : scheme.outlineVariant,
          ),
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        margin: const EdgeInsets.symmetric(vertical: 6),
        color: scheme.surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radius),
          side: BorderSide(color: isLight ? borderLight : scheme.outlineVariant),
        ),
      ),
      chipTheme: ChipThemeData(
        shape: const StadiumBorder(),
        side: BorderSide(color: isLight ? borderLight : scheme.outlineVariant),
        labelStyle: TextStyle(
          fontSize: 12,
          color: isLight ? const Color(0xFF33475B) : scheme.onSurfaceVariant,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: false,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: isLight ? borderLight : scheme.outlineVariant),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: scheme.primary, width: 1.5),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      ),
      dividerTheme: DividerThemeData(
        color: isLight ? borderLight : scheme.outlineVariant,
        thickness: 1,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 18),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 18),
        ),
      ),
      listTileTheme: ListTileThemeData(
        iconColor: isLight ? const Color(0xFF33475B) : scheme.onSurfaceVariant,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(radius)),
      ),
    );
  }
}
