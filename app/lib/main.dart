import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'app/navigation.dart';
import 'app/router.dart';
import 'app/theme/app_theme.dart';
import 'core/app_services.dart';
import 'core/network/api_client.dart';
import 'core/notifications/local_notifications.dart';
import 'core/notifications/push_service.dart';
import 'core/settings/app_settings.dart';
import 'core/storage/token_store.dart';
import 'features/announcements/data/announcements_api.dart';
import 'features/attendance/data/attendance_api.dart';
import 'features/auth/data/auth_repository.dart';
import 'features/auth/presentation/session.dart';
import 'features/excuses/data/excuses_api.dart';
import 'features/grades/data/grade_entry_api.dart';
import 'features/grades/data/grades_api.dart';
import 'features/identity/data/identity_api.dart';
import 'features/materials/data/materials_api.dart';
import 'features/notifications/data/notifications_api.dart';
import 'features/notifications/presentation/inbox_page.dart';
import 'features/requests/data/requests_api.dart';
import 'features/settings/data/two_factor_api.dart';
import 'features/timetable/data/timetable_api.dart';
import 'l10n/app_localizations.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // الإعدادات تُحمَّل قبل أول إطار كي لا يظهر التطبيق بلغة ثم يتبدّل
  final settings = await AppSettings.load();
  final store = TokenStore();
  final dio = buildDio();
  final authApi = HttpAuthApi(dio: dio, store: store);
  final services = AppServices(
    auth: authApi,
    attendance: HttpAttendanceApi(dio: dio, store: store),
    timetable: HttpTimetableApi(dio: dio, store: store),
    materials: HttpMaterialsApi(dio: dio, store: store),
    grades: HttpGradesApi(dio: dio, store: store),
    gradeEntry: HttpGradeEntryApi(dio: dio, store: store),
    announcements: HttpAnnouncementsApi(dio: dio, store: store),
    notifications: HttpNotificationsApi(dio: dio, store: store),
    excuses: HttpExcusesApi(dio: dio, store: store),
    requests: HttpRequestsApi(dio: dio, store: store),
    identity: HttpIdentityApi(dio: dio, store: store),
    twoFactor: HttpTwoFactorApi(dio: dio, store: store),
  );
  final session = SessionController(authApi);

  // الضغط على أي إشعار (نظام أو دفع) يفتح صندوق الإشعارات فوق الشاشة الحالية
  void openInbox(String? _) {
    if (!session.isAuthenticated) {
      return;
    }
    final navigator = rootNavigatorKey.currentState;
    if (navigator == null) {
      return;
    }
    navigator.push(
      MaterialPageRoute<void>(
        builder: (_) => InboxPage(api: services.notifications, session: session),
      ),
    );
  }

  final reminders = LocalNotificationService(onTap: openInbox);
  final push = PushService(
    notifications: services.notifications,
    local: reminders,
    onOpen: openInbox,
  );

  runApp(
    CsitApp(
      session: session,
      services: services,
      settings: settings,
      reminders: reminders,
      push: push,
    ),
  );
}

class CsitApp extends StatefulWidget {
  const CsitApp({
    super.key,
    required this.session,
    required this.services,
    required this.settings,
    this.reminders,
    this.push,
  });

  final SessionController session;
  final AppServices services;
  final AppSettings settings;
  final LocalNotificationService? reminders;
  final PushService? push;

  @override
  State<CsitApp> createState() => _CsitAppState();
}

class _CsitAppState extends State<CsitApp> {
  late final GoRouter _router = createRouter(
    widget.session,
    widget.services,
    widget.settings,
    reminders: widget.reminders,
    push: widget.push,
  );

  @override
  void initState() {
    super.initState();
    // استعادة الجلسة عند الإقلاع (إن وُجد رمز تجديد صالح).
    widget.session.restore();
  }

  @override
  void dispose() {
    _router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: widget.settings,
      builder: (context, _) => MaterialApp.router(
        onGenerateTitle: (context) => AppLocalizations.of(context)!.appTitle,
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        darkTheme: AppTheme.dark,
        themeMode: widget.settings.themeMode,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: widget.settings.locale,
        routerConfig: _router,
      ),
    );
  }
}
