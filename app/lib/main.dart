import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'app/router.dart';
import 'app/theme/app_theme.dart';
import 'core/app_services.dart';
import 'core/network/api_client.dart';
import 'core/storage/token_store.dart';
import 'features/announcements/data/announcements_api.dart';
import 'features/attendance/data/attendance_api.dart';
import 'features/auth/data/auth_repository.dart';
import 'features/auth/presentation/session.dart';
import 'features/grades/data/grades_api.dart';
import 'features/materials/data/materials_api.dart';
import 'features/notifications/data/notifications_api.dart';
import 'features/timetable/data/timetable_api.dart';
import 'l10n/app_localizations.dart';

void main() {
  final store = TokenStore();
  final dio = buildDio();
  final authApi = HttpAuthApi(dio: dio, store: store);
  final services = AppServices(
    auth: authApi,
    attendance: HttpAttendanceApi(dio: dio, store: store),
    timetable: HttpTimetableApi(dio: dio, store: store),
    materials: HttpMaterialsApi(dio: dio, store: store),
    grades: HttpGradesApi(dio: dio, store: store),
    announcements: HttpAnnouncementsApi(dio: dio, store: store),
    notifications: HttpNotificationsApi(dio: dio, store: store),
  );
  runApp(CsitApp(session: SessionController(authApi), services: services));
}

class CsitApp extends StatefulWidget {
  const CsitApp({super.key, required this.session, required this.services});

  final SessionController session;
  final AppServices services;

  @override
  State<CsitApp> createState() => _CsitAppState();
}

class _CsitAppState extends State<CsitApp> {
  late final GoRouter _router =
      createRouter(widget.session, widget.services);

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
    return MaterialApp.router(
      onGenerateTitle: (context) => AppLocalizations.of(context)!.appTitle,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('ar'),
      routerConfig: _router,
    );
  }
}
