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
  String get homeTodayLectures => 'محاضرات اليوم';

  @override
  String get homeNoLectures => 'لا محاضرات اليوم';

  @override
  String get homeLatestAnnouncement => 'آخر إعلان';

  @override
  String get homeViewAll => 'عرض الكل';

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

  @override
  String get timetableTitle => 'الجدول الأسبوعي';

  @override
  String get timetableEmpty => 'لا توجد محاضرات في هذه الفترة';

  @override
  String timetableOffline(String time) {
    return 'تعذر الاتصال؛ تُعرض بيانات محفوظة من $time';
  }

  @override
  String get changeCancelled => 'ملغاة';

  @override
  String get changeMoved => 'نُقلت';

  @override
  String get changeExtra => 'إضافة';

  @override
  String get weekdaySunday => 'الأحد';

  @override
  String get weekdayMonday => 'الاثنين';

  @override
  String get weekdayTuesday => 'الثلاثاء';

  @override
  String get weekdayWednesday => 'الأربعاء';

  @override
  String get weekdayThursday => 'الخميس';

  @override
  String get weekdayFriday => 'الجمعة';

  @override
  String get weekdaySaturday => 'السبت';

  @override
  String get courseMaterialsTitle => 'مواد المقررات';

  @override
  String get noOfferings => 'لا توجد مواد دراسية مسجَّلة';

  @override
  String get courseMaterialsEmpty => 'لا مواد منشورة بعد';

  @override
  String get materialsDownload => 'تنزيل';

  @override
  String get materialsOpenLink => 'فتح';

  @override
  String get materialsLinkOpenFailed => 'تعذر فتح الرابط؛ حاول مجدداً';

  @override
  String materialsWeek(int week) {
    return 'الأسبوع $week';
  }

  @override
  String get gradesTitle => 'درجاتك';

  @override
  String get gradesEmpty => 'لا درجات منشورة بعد';

  @override
  String get notGradedYet => 'لم تُرصد';

  @override
  String weightedOfTotal(String total, String sum) {
    return '$total من $sum';
  }

  @override
  String scoreOfMax(String score, String max) {
    return '$score / $max';
  }

  @override
  String weightShort(String weight) {
    return 'وزن $weight%';
  }

  @override
  String get timetableCard => 'الجدول';

  @override
  String get timetableCardHint => 'محاضراتك وتغييراتها المؤرخة';

  @override
  String get materialsCardHint => 'ملفات المحاضرات وروابطها';

  @override
  String get gradesCardHint => 'نتائجك المنشورة والمجموع الموزون';

  @override
  String get gradeEntryTitle => 'إدخال الدرجات';

  @override
  String get gradeEntryHint =>
      'أدخل درجات التقييم كمسودة، والنشر يتم بموافقة الكلية';

  @override
  String get chooseOfferingLabel => 'المادة';

  @override
  String get chooseAssessmentLabel => 'التقييم';

  @override
  String get noAssessmentsYet => 'لا تقييمات بعد — أنشئ تقييماً أولاً';

  @override
  String get newAssessmentButton => 'تقييم جديد';

  @override
  String get assessmentNameLabel => 'اسم التقييم';

  @override
  String get assessmentKindLabel => 'النوع';

  @override
  String get maxScoreLabel => 'الدرجة العظمى';

  @override
  String get weightPercentLabel => 'الوزن %';

  @override
  String get createAssessmentButton => 'إنشاء التقييم';

  @override
  String get assessmentCreated => 'أُنشئ التقييم';

  @override
  String gradedOfTotal(int graded, int total) {
    return 'أُدخلت $graded من $total درجة';
  }

  @override
  String get saveDraftButton => 'حفظ كمسودة';

  @override
  String get draftSaved => 'حُفظت المسودة';

  @override
  String get publishGradesButton => 'نشر الدرجات';

  @override
  String get publishNeedsAdmin => 'النشر يتطلب موافقة مدير الكلية';

  @override
  String publishedSuccess(int count) {
    return 'نُشرت الدرجات وأُشعر $count طالباً';
  }

  @override
  String scoreRangeError(String max) {
    return 'الدرجة يجب أن تكون بين 0 و$max';
  }

  @override
  String get assessmentLocked => 'التقييم منشور — لا يمكن تعديل درجاته';

  @override
  String get assessmentPublished => 'منشور';

  @override
  String get kindQuiz => 'كوز';

  @override
  String get kindLab => 'مختبر';

  @override
  String get kindMidterm => 'نصفي';

  @override
  String get kindFinal => 'نهائي';

  @override
  String get kindOther => 'أخرى';

  @override
  String get assessmentWeightHint => 'مجموع أوزان التقييمات لا يتجاوز 100%';

  @override
  String get loginTotpLabel => 'رمز التحقق بخطوتين';

  @override
  String get loginTotpHint =>
      'أدخل الرمز من تطبيق المصادقة (يتطلبه حساب التدريسي/الإدارة)';

  @override
  String get totpRequiredError =>
      'هذا الحساب محمي بالتحقق بخطوتين؛ أدخل الرمز ثم أعد المحاولة';

  @override
  String get totpInvalidError => 'رمز التحقق غير صحيح أو انتهت صلاحيته';

  @override
  String get announcementsCard => 'الإعلانات';

  @override
  String get announcementsCardHint => 'أخبار الكلية وقسمك وموادك';

  @override
  String get announcementsTitle => 'الإعلانات';

  @override
  String get announcementsEmpty => 'لا إعلانات منشورة حالياً';

  @override
  String get announcementPinned => 'مثبَّت';

  @override
  String get announcementPriorityHigh => 'مهم';

  @override
  String get announcementMarkedRead => 'تم تعليم الإعلان كمقروء';

  @override
  String get announcementUnknownScope => 'إعلان';

  @override
  String get inboxCard => 'الإشعارات';

  @override
  String get inboxCardHint => 'صندوق الوارد وتنبيهات الأجهزة';

  @override
  String get inboxTitle => 'الإشعارات';

  @override
  String get inboxEmpty => 'لا إشعارات بعد';

  @override
  String get markAllRead => 'تعليم الكل كمقروء';

  @override
  String unreadBadge(int count) {
    return '$count جديد';
  }

  @override
  String get notificationsPermissionDenied =>
      'لم يُمنح إذن الإشعارات؛ يمكنك متابعتها داخل التطبيق';

  @override
  String get notificationsEnabledMessage =>
      'تم تفعيل إشعارات المحاضرات على هذا الجهاز';

  @override
  String get reminderLectureTitle => 'محاضرة بعد 15 دقيقة';

  @override
  String reminderLectureBody(String course, String room, String time) {
    return '$course — $room الساعة $time';
  }

  @override
  String get reminderDigestTitle => 'محاضرات الغد';

  @override
  String reminderDigestBody(int count, String time) {
    return '$count محاضرة تبدأ الساعة $time';
  }

  @override
  String get reminderDigestEmpty => 'لا محاضرات غداً';

  @override
  String get reminderChannelName => 'تذكيرات المحاضرات';

  @override
  String get reminderChannelDescription =>
      'تذكير قبل المحاضرة وملخص محاضرات الغد';

  @override
  String get excusesCard => 'الأعذار';

  @override
  String get excusesCardHint => 'رفع عذر غياب ومتابعة قراره';

  @override
  String get excusesTitle => 'أعذاري';

  @override
  String get excusesEmpty => 'لا أعذار مرفوعة';

  @override
  String get excuseNewTitle => 'عذر غياب جديد';

  @override
  String get excuseSessionLabel => 'المحاضرة';

  @override
  String get excuseSelectSession => 'اختر المحاضرة الغائبة';

  @override
  String get excuseNoSessions =>
      'لا محاضرات مؤهلة لرفع عذر (لا غياب خلال 14 يوماً)';

  @override
  String get excuseReasonLabel => 'سبب الغياب';

  @override
  String get excuseReasonHint =>
      'اشرح السبب بإيجاز، وأرفق صورة التقرير إن وُجد';

  @override
  String get excuseAttach => 'إرفاق صورة أو PDF';

  @override
  String get excuseAttachCamera => 'التقاط صورة';

  @override
  String get excuseAttachGallery => 'من المعرض';

  @override
  String get excuseAttachmentChosen => 'تم اختيار المرفق';

  @override
  String get excuseSubmit => 'إرسال العذر';

  @override
  String get excuseSubmitted => 'أُرسل العذر للمراجعة';

  @override
  String get excuseStatusPending => 'قيد المراجعة';

  @override
  String get excuseStatusApproved => 'مقبول';

  @override
  String get excuseStatusRejected => 'مرفوض';

  @override
  String get excuseReviewNote => 'ملاحظة المراجع';

  @override
  String get excuseWithdraw => 'سحب العذر';

  @override
  String get excuseWithdrawn => 'تم سحب العذر';

  @override
  String get excuseWindowClosed =>
      'انتهت مدة رفع العذر لهذه المحاضرة (14 يوماً)';

  @override
  String get excuseReviewTitle => 'مراجعة الأعذار';

  @override
  String get excuseReviewEmpty => 'لا أعذار تنتظر المراجعة';

  @override
  String get excuseApprove => 'قبول';

  @override
  String get excuseReject => 'رفض';

  @override
  String get excuseReviewNoteHint => 'ملاحظة تظهر للطالب (اختياري)';

  @override
  String get excuseReviewed => 'تم تسجيل القرار';

  @override
  String excusePendingCount(int count) {
    return 'بانتظار المراجعة: $count';
  }

  @override
  String get requestsCard => 'الطلبات';

  @override
  String get requestsCardHint => 'تواصل مع قسمك بشأن دراستك';

  @override
  String get requestsTitle => 'طلباتي';

  @override
  String get requestsEmpty => 'لا طلبات بعد';

  @override
  String get requestNewTitle => 'طلب جديد';

  @override
  String get requestCategoryLabel => 'التصنيف';

  @override
  String get requestCategoryAcademic => 'مسألة أكاديمية';

  @override
  String get requestCategorySchedule => 'الجدول والقاعات';

  @override
  String get requestCategoryGrades => 'درجة أو تقييم';

  @override
  String get requestCategoryDocuments => 'وثيقة أو تأييد';

  @override
  String get requestCategoryOther => 'أخرى';

  @override
  String get requestSubjectLabel => 'الموضوع';

  @override
  String get requestBodyLabel => 'تفاصيل الطلب';

  @override
  String get requestSend => 'إرسال الطلب';

  @override
  String get requestCreated => 'أُرسل طلبك إلى قسمك';

  @override
  String get requestDetailTitle => 'تفاصيل الطلب';

  @override
  String get requestReplyHint => 'اكتب رسالتك…';

  @override
  String get requestSendReply => 'إرسال';

  @override
  String get requestClosedNotice => 'الطلب مغلق؛ لا يمكن إضافة رسائل';

  @override
  String get requestStatusOpen => 'مفتوح';

  @override
  String get requestStatusInProgress => 'قيد المعالجة';

  @override
  String get requestStatusResolved => 'تم الحل';

  @override
  String get requestStatusClosed => 'مغلق';

  @override
  String get conversationEmpty => 'لا رسائل بعد';

  @override
  String get identityCard => 'الهوية الرقمية';

  @override
  String get identityCardHint => 'بطاقة QR موقّعة تُثبت هويتك في الامتحان';

  @override
  String get identityTitle => 'بطاقتك الرقمية';

  @override
  String get identityCardNote =>
      'اعرض البطاقة للتدريسي أو بوابة القاعة. تتجدد تلقائياً ولا تعمل لقطة الشاشة القديمة.';

  @override
  String identityValidFor(int seconds) {
    return 'صالحة $seconds ثانية';
  }

  @override
  String get identityRefreshButton => 'تحديث البطاقة';

  @override
  String get identityVerifyTitle => 'التحقق من بطاقة طالب';

  @override
  String get identityVerifyHint => 'وجّه الكاميرا إلى بطاقة الطالب الرقمية';

  @override
  String get identityVerifyButton => 'تحقق';

  @override
  String get identityValidTitle => 'بطاقة صالحة';

  @override
  String get identityInvalidTitle => 'بطاقة غير صالحة';

  @override
  String get identityStudentLabel => 'الطالب';

  @override
  String get identityStudyTypeMorning => 'صباحي';

  @override
  String get identityStudyTypeEvening => 'مسائي';

  @override
  String get identityCardForStaffOnly =>
      'التحقق من البطاقات متاح للتدريسي والإدارة';

  @override
  String get identityExpiredError =>
      'انتهت صلاحية البطاقة؛ اطلب من الطالب تحديثها';

  @override
  String get settingsCard => 'الإعدادات';

  @override
  String get settingsCardHint => 'المظهر واللغة والتحقق بخطوتين';

  @override
  String get settingsTitle => 'الإعدادات';

  @override
  String get settingsAppearance => 'المظهر';

  @override
  String get settingsThemeLight => 'فاتح';

  @override
  String get settingsThemeDark => 'داكن';

  @override
  String get settingsThemeSystem => 'حسب النظام';

  @override
  String get settingsLanguage => 'اللغة';

  @override
  String get settingsLanguageArabic => 'العربية';

  @override
  String get settingsLanguageEnglish => 'English';

  @override
  String get settingsSaved => 'تم حفظ الإعدادات';

  @override
  String get settingsNotifications => 'إشعارات المحاضرات';

  @override
  String get settingsNotificationsHint =>
      'تذكير قبل 15 دقيقة وملخص محاضرات الغد';

  @override
  String get settingsNotificationsOn => 'مفعّلة على هذا الجهاز';

  @override
  String get settingsNotificationsOff => 'غير مفعّلة';

  @override
  String get enableNotificationsButton => 'تفعيل الإشعارات';

  @override
  String get twoFactorTitle => 'التحقق بخطوتين';

  @override
  String get twoFactorHint =>
      'حماية إضافية لحساب التدريسي والإدارة عبر تطبيق مصادقة';

  @override
  String get twoFactorEnabled => 'مفعّل';

  @override
  String get twoFactorDisabled => 'غير مفعّل';

  @override
  String get twoFactorSetup => 'بدء الإعداد';

  @override
  String get twoFactorSecretLabel => 'السرّ (أدخله يدوياً إن لم يقرأ الرمز)';

  @override
  String get twoFactorCodeLabel => 'رمز التطبيق (6 أرقام)';

  @override
  String get twoFactorEnable => 'تفعيل';

  @override
  String get twoFactorDisable => 'تعطيل';

  @override
  String get twoFactorPasswordLabel => 'كلمة المرور لتأكيد التعطيل';

  @override
  String get twoFactorEnabledMessage => 'تم تفعيل التحقق بخطوتين';

  @override
  String get twoFactorDisabledMessage => 'تم تعطيل التحقق بخطوتين';

  @override
  String get twoFactorNotAvailable => 'متاح لحساب التدريسي والإدارة فقط';

  @override
  String get twoFactorSetupHint =>
      'أضف السرّ إلى تطبيق Google Authenticator أو أي تطبيق TOTP ثم أدخل الرمز الظاهر.';

  @override
  String dataFromCache(String time) {
    return 'تعذر الاتصال؛ تُعرض بيانات محفوظة من $time';
  }

  @override
  String get offlineSavedHint => 'تُحدَّث البيانات تلقائياً عند عودة الاتصال';
}
