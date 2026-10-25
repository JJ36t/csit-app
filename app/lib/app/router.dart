import 'package:go_router/go_router.dart';

import '../../features/attendance/data/attendance_api.dart';
import '../../features/auth/presentation/login_page.dart';
import '../../features/auth/presentation/session.dart';
import '../../features/home/presentation/home_page.dart';

/// ملاحة محمية بالجلسة: لا وصول للرئيسية قبل الدخول، ولا رجوع للدخول بعد نجاحه.
GoRouter createRouter(SessionController session, AttendanceApi attendance) {
  return GoRouter(
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
        builder: (context, state) =>
            HomePage(session: session, attendance: attendance),
      ),
    ],
  );
}
