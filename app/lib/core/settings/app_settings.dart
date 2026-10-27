import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// إعدادات المستخدم المحلية: اللغة (عربي/إنجليزي) والمظهر (فاتح/داكن/النظام).
///
/// تُحفظ في SharedPreferences وتُحمَّل قبل `runApp` كي لا يظهر التطبيق
/// بلغة ثم يتبدّل بعد أول إطار (وميض الترجمة).
class AppSettings extends ChangeNotifier {
  AppSettings._(this._prefs, this._localeCode, this._themeMode);

  static const _localeKey = 'csit.settings.locale';
  static const _themeKey = 'csit.settings.theme';
  static const supportedLocales = ['ar', 'en'];

  final SharedPreferences _prefs;
  String _localeCode;
  ThemeMode _themeMode;

  static Future<AppSettings> load() async {
    final prefs = await SharedPreferences.getInstance();
    final code = prefs.getString(_localeKey);
    return AppSettings._(
      prefs,
      supportedLocales.contains(code) ? code! : 'ar',
      themeModeFrom(prefs.getString(_themeKey)),
    );
  }

  /// للاختبارات: بناء من كائن SharedPreferences مُهيّأ مسبقاً.
  factory AppSettings.fromPrefs(SharedPreferences prefs) => AppSettings._(
        prefs,
        supportedLocales.contains(prefs.getString(_localeKey))
            ? prefs.getString(_localeKey)!
            : 'ar',
        themeModeFrom(prefs.getString(_themeKey)),
      );

  String get localeCode => _localeCode;

  Locale get locale => Locale(_localeCode);

  bool get isArabic => _localeCode == 'ar';

  ThemeMode get themeMode => _themeMode;

  Future<void> setLocale(String code) async {
    if (code == _localeCode || !supportedLocales.contains(code)) {
      return;
    }
    _localeCode = code;
    notifyListeners();
    await _prefs.setString(_localeKey, code);
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    if (mode == _themeMode) {
      return;
    }
    _themeMode = mode;
    notifyListeners();
    await _prefs.setString(_themeKey, themeModeName(mode));
  }

  static String themeModeName(ThemeMode mode) => switch (mode) {
        ThemeMode.light => 'light',
        ThemeMode.dark => 'dark',
        _ => 'system',
      };

  static ThemeMode themeModeFrom(String? value) => switch (value) {
        'light' => ThemeMode.light,
        'dark' => ThemeMode.dark,
        _ => ThemeMode.system,
      };
}
