import 'package:go_router/go_router.dart';

import '../../features/auth/presentation/login_page.dart';
import '../../features/auth/presentation/session.dart';
import '../../features/home/presentation/home_page.dart';
import '../core/app_services.dart';
import '../core/notifications/local_notifications.dart';
import '../core/notifications/push_service.dart';
import '../core/settings/app_settings.dart';
import 'navigation.dart';

/// ملاحة محمية بالجلسة: لا وصول للرئيسية قبل الدخول، ولا رجوع للدخول بعد نجاحه.
GoRouter createRouter(
  SessionController session,
  AppServices services,
  AppSettings settings, {
  LocalNotificationService? reminders,
  PushService? push,
}) {
  return GoRouter(
    navigatorKey: rootNavigatorKey,
    initialLocation: '/login',
    refreshListenable: session,
    redirect: (context, state) {
      final atLogin = state.matchedLocation == '/login';
      if (!session.isAuthenticated) {
        return atLogin ? null : '/login';
      }
      return atLogin ? '/home' : null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => LoginPage(session: session)),
      GoRoute(
        path: '/home',
        builder: (context, state) => HomePage(
          session: session,
          services: services,
          settings: settings,
          reminders: reminders,
          push: push,
        ),
      ),
    ],
  );
}
