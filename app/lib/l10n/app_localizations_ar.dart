// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Arabic (`ar`).
class AppLocalizationsAr extends AppLocalizations {
  AppLocalizationsAr([String locale = 'ar']) : super(locale);

  @override
  String get appTitle => 'علوم الحاسوب';

  @override
  String get collegeName =>
      'كلية علوم الحاسوب وتكنولوجيا المعلومات — جامعة القادسية';

  @override
  String get loginTitle => 'تسجيل الدخول';

  @override
  String get loginSubtitle =>
      'استخدم الرقم الجامعي وكلمة المرور التي زوّدك بها قسمك';

  @override
  String get universityIdLabel => 'الرقم الجامعي';

  @override
  String get passwordLabel => 'كلمة المرور';

  @override
  String get loginButton => 'دخول';

  @override
  String get fieldRequired => 'هذا الحقل مطلوب';

  @override
  String get universityIdInvalid =>
      'الرقم الجامعي يجب أن يكون 3 محارف على الأقل';

  @override
  String get networkUnreachable =>
      'تعذر الاتصال بالخادم؛ تحقق من الإنترنت وحاول مجدداً';

  @override
  String get unexpectedError => 'حدث خطأ غير متوقع؛ أعد المحاولة';

  @override
  String get sessionExpired => 'انتهت الجلسة؛ يرجى تسجيل الدخول من جديد';

  @override
  String get homeTitle => 'الرئيسية';

  @override
  String get welcome => 'أهلاً';

  @override
  String get logoutButton => 'تسجيل الخروج';

  @override
  String get mustChangePasswordNotice => 'يُطلب منك تغيير كلمة المرور الأولية';

  @override
  String get changePasswordTitle => 'تغيير كلمة المرور';

  @override
  String get changePasswordButton => 'حفظ كلمة المرور';

  @override
  String get currentPasswordLabel => 'كلمة المرور الحالية';

  @override
  String get newPasswordLabel => 'كلمة المرور الجديدة';

  @override
  String get passwordTooShort => 'كلمة المرور يجب ألا تقل عن 8 محارف';

  @override
  String get passwordChanged => 'تم تغيير كلمة المرور؛ سجّل الدخول من جديد';

  @override
  String get departmentLabel => 'القسم';

  @override
  String get stageLabel => 'المرحلة';

  @override
  String get groupLabel => 'الشعبة';

  @override
  String get scanAttendanceCard => 'مسح الحضور';

  @override
  String get scanAttendanceCardHint => 'امسح رمز الجلسة لتسجيل حضورك';

  @override
  String get todaySessionsCard => 'حصص اليوم';

  @override
  String get todaySessionsCardHint => 'افتح الجلسة وتابع الحضور لحظياً';

  @override
  String get todaySessionsTitle => 'حصص اليوم';

  @override
  String get noSessionsToday => 'لا توجد حصص مجدولة لك اليوم';

  @override
  String get noStudentsInFilter => 'لا يوجد طلاب في هذه الحالة';

  @override
  String get retryButton => 'إعادة المحاولة';

  @override
  String get scanTitle => 'مسح الحضور';

  @override
  String get scannerHint => 'ضع رمز الجلسة داخل الإطار';

  @override
  String get scanHelp =>
      'وجّه الكاميرا إلى رمز الجلسة المعروض عند التدريسي. يتجدد الرمز كل 20 ثانية.';

  @override
  String get lastScanResult => 'نتيجة آخر مسح';

  @override
  String get presentStatus => 'حاضر';

  @override
  String get lateStatus => 'متأخر';

  @override
  String get absentStatus => 'غائب';

  @override
  String get excusedStatus => 'غياب بعذر';

  @override
  String get flaggedStatus => 'مشكوك';

  @override
  String get notRecordedStatus => 'لم يُسجّل';

  @override
  String get deviceNote =>
      'المسح مرتبط بجهازك المسجّل · لا يمكن المسح من جهاز آخر';

  @override
  String get invalidQrError => 'الرمز الممسوح ليس رمز حضور صالحاً لهذا التطبيق';

  @override
  String get missingDeviceError =>
      'معلومات جهازك غير مكتملة؛ سجّل الدخول من جديد ثم أعد المحاولة';

  @override
  String get flagNoLocation =>
      'لم يُرسَل موقع الجهاز مع المسح؛ سيراجع التدريسي الحضور';

  @override
  String flagOutsideCampus(int meters) {
    return 'الموقع خارج نطاق القاعة (نحو $metersم)؛ سيراجع التدريسي الحضور';
  }

  @override
  String get liveTitle => 'قائمة الحاضرين';

  @override
  String get liveAttendance => 'الحضور اللحظي';

  @override
  String get qrRenewsChip => 'الرمز يتجدد تلقائياً';

  @override
  String presentOfTotal(int present, int total) {
    return '$present حاضراً من $total';
  }

  @override
  String percentValue(int percent) {
    return '$percent%';
  }

  @override
  String lateCount(int count) {
    return 'متأخر $count';
  }

  @override
  String flaggedCount(int count) {
    return 'مشكوك $count';
  }

  @override
  String absentCount(int count) {
    return 'غائب $count';
  }

  @override
  String get filterAll => 'الكل';

  @override
  String get sessionKindTheory => 'نظري';

  @override
  String get sessionKindLab => 'مختبر';

  @override
  String get sessionStatusOpen => 'الجلسة مفتوحة';

  @override
  String get sessionStatusClosed => 'أُغلقت الجلسة';

  @override
  String get sessionStatusScheduled => 'لم تُفتح بعد';

  @override
  String get sessionStatusCancelled => 'ملغاة';

  @override
  String get openSessionButton => 'فتح الجلسة';

  @override
  String get openSessionHint =>
      'افتح الجلسة عند بدء المحاضرة ليبدأ استقبال المسح ويظهر الرمز للطلبة.';

  @override
  String get closeSessionButton => 'إغلاق الجلسة';

  @override
  String get closeSessionNote => 'إغلاق الجلسة يوقف استقبال المسح فوراً.';

  @override
  String get closeSessionConfirmTitle => 'إغلاق الجلسة؟';

  @override
  String get closeSessionConfirmBody =>
      'سيُسجَّل غياب من لم يسجّل حضوره، ويتوقف استقبال المسح فوراً.';

  @override
  String get confirmButton => 'تأكيد';

  @override
  String get cancelButton => 'إلغاء';

  @override
  String absentMarkedNote(int count) {
    return 'سُجّل غياب $count طالباً لم يسجّلوا حضورهم.';
  }
}
