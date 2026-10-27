import '../features/announcements/data/announcements_api.dart';
import '../features/attendance/data/attendance_api.dart';
import '../features/auth/data/auth_repository.dart';
import '../features/excuses/data/excuses_api.dart';
import '../features/grades/data/grade_entry_api.dart';
import '../features/grades/data/grades_api.dart';
import '../features/identity/data/identity_api.dart';
import '../features/materials/data/materials_api.dart';
import '../features/notifications/data/notifications_api.dart';
import '../features/requests/data/requests_api.dart';
import '../features/settings/data/two_factor_api.dart';
import '../features/timetable/data/timetable_api.dart';

/// حزمة واجهات الخدمة التي تعتمد عليها الشاشات — تُبنى مرة في `main`
/// وتُحقن في الموجّه والرئيسية، فتُختبر الشاشات ببدائل في الذاكرة.
class AppServices {
  const AppServices({
    required this.auth,
    required this.attendance,
    required this.timetable,
    required this.materials,
    required this.grades,
    required this.gradeEntry,
    required this.announcements,
    required this.notifications,
    required this.excuses,
    required this.requests,
    required this.identity,
    required this.twoFactor,
  });

  final AuthApi auth;
  final AttendanceApi attendance;
  final TimetableApi timetable;
  final MaterialsApi materials;
  final GradesApi grades;
  final GradeEntryApi gradeEntry;
  final AnnouncementsApi announcements;
  final NotificationsApi notifications;
  final ExcusesApi excuses;
  final RequestsApi requests;
  final IdentityApi identity;
  final TwoFactorApi twoFactor;
}
