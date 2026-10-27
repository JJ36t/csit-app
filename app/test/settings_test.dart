import 'package:csit/core/network/api_client.dart';
import 'package:csit/core/settings/app_settings.dart';
import 'package:csit/features/auth/data/auth_repository.dart';
import 'package:csit/features/auth/presentation/session.dart';
import 'package:csit/features/settings/data/two_factor_api.dart';
import 'package:csit/features/settings/presentation/settings_page.dart';
import 'package:csit/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _AuthStub implements AuthApi {
  @override
  Future<UserProfile> login({
    required String universityId,
    required String password,
    String? totpCode,
  }) async =>
      throw ApiException('unused', null);

  @override
  Future<UserProfile> me() async => throw ApiException('unused', null);

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {}

  @override
  Future<void> logout() async {}

  @override
  Future<bool> hasSession() async => false;
}

class _TwoFactorStub implements TwoFactorApi {
  _TwoFactorStub({this.enabled = false});

  bool enabled;
  bool available = true;

  @override
  Future<TwoFactorStatus> status() async =>
      TwoFactorStatus(enabled: enabled, available: available);

  @override
  Future<TwoFactorSetup> setup() async =>
      const TwoFactorSetup(secret: 'ABC234', otpauthUri: 'otpauth://totp/x');

  @override
  Future<void> enable(String code) async => enabled = true;

  @override
  Future<void> disable(String password) async => enabled = false;
}

Widget _wrap(Widget child, AppSettings settings) {
  return ListenableBuilder(
    listenable: settings,
    builder: (context, _) => MaterialApp(
      locale: settings.locale,
      theme: ThemeData.light(),
      darkTheme: ThemeData.dark(),
      themeMode: settings.themeMode,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    ),
  );
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('الافتراضي عربي ومظهر النظام ثم يُحفظ الاختيار', () async {
    final settings = await AppSettings.load();
    expect(settings.localeCode, 'ar');
    expect(settings.themeMode, ThemeMode.system);

    await settings.setLocale('en');
    await settings.setThemeMode(ThemeMode.dark);

    final reloaded = await AppSettings.load();
    expect(reloaded.localeCode, 'en');
    expect(reloaded.themeMode, ThemeMode.dark);
    expect(reloaded.locale, const Locale('en'));
  });

  test('قيمة لغة غير مدعومة تُتجاهل', () async {
    final settings = await AppSettings.load();
    await settings.setLocale('fr');
    expect(settings.localeCode, 'ar');
  });

  testWidgets('اختيار الوضع الداكن يحدّث السمة فوراً', (tester) async {
    final settings = await AppSettings.load();
    final session = SessionController(_AuthStub());
    await tester.pumpWidget(
      _wrap(
        SettingsPage(
          settings: settings,
          twoFactor: _TwoFactorStub(enabled: true),
          session: session,
        ),
        settings,
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('داكن'));
    await tester.pumpAndSettle();

    expect(settings.themeMode, ThemeMode.dark);
    expect(
      Theme.of(tester.element(find.text('الإعدادات'))).brightness,
      Brightness.dark,
    );
  });

  testWidgets('تبديل اللغة يعيد بناء الواجهة بالإنجليزية', (tester) async {
    final settings = await AppSettings.load();
    final session = SessionController(_AuthStub());
    await tester.pumpWidget(
      _wrap(
        SettingsPage(
          settings: settings,
          twoFactor: _TwoFactorStub(),
          session: session,
        ),
        settings,
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('الإعدادات'), findsOneWidget);

    await tester.tap(find.text('English'));
    await tester.pumpAndSettle();

    expect(settings.localeCode, 'en');
    expect(find.text('Settings'), findsOneWidget);
  });

  testWidgets('تفعيل التحقق بخطوتين يطلب السرّ والرمز', (tester) async {
    final settings = await AppSettings.load();
    final api = _TwoFactorStub();
    final session = SessionController(_AuthStub());
    await tester.pumpWidget(
      _wrap(
        SettingsPage(settings: settings, twoFactor: api, session: session),
        settings,
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('setupTwoFactorButton')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('twoFactorSecret')), findsOneWidget);
    await tester.enterText(find.byKey(const Key('twoFactorCodeField')), '123456');
    await tester.tap(find.text('تفعيل'));
    await tester.pumpAndSettle();

    expect(api.enabled, isTrue);
  });
}
