import '../features/attendance/data/attendance_api.dart';
import '../features/auth/data/auth_repository.dart';
import '../features/grades/data/grades_api.dart';
import '../features/materials/data/materials_api.dart';
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
  });

  final AuthApi auth;
  final AttendanceApi attendance;
  final TimetableApi timetable;
  final MaterialsApi materials;
  final GradesApi grades;
}
