import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_ar.dart';
import 'app_localizations_en.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('ar'),
    Locale('en')
  ];

  /// No description provided for @appTitle.
  ///
  /// In ar, this message translates to:
  /// **'علوم الحاسوب'**
  String get appTitle;

  /// No description provided for @collegeName.
  ///
  /// In ar, this message translates to:
  /// **'كلية علوم الحاسوب وتكنولوجيا المعلومات — جامعة القادسية'**
  String get collegeName;

  /// No description provided for @loginTitle.
  ///
  /// In ar, this message translates to:
  /// **'تسجيل الدخول'**
  String get loginTitle;

  /// No description provided for @loginSubtitle.
  ///
  /// In ar, this message translates to:
  /// **'استخدم الرقم الجامعي وكلمة المرور التي زوّدك بها قسمك'**
  String get loginSubtitle;

  /// No description provided for @universityIdLabel.
  ///
  /// In ar, this message translates to:
  /// **'الرقم الجامعي'**
  String get universityIdLabel;

  /// No description provided for @passwordLabel.
  ///
  /// In ar, this message translates to:
  /// **'كلمة المرور'**
  String get passwordLabel;

  /// No description provided for @loginButton.
  ///
  /// In ar, this message translates to:
  /// **'دخول'**
  String get loginButton;

  /// No description provided for @fieldRequired.
  ///
  /// In ar, this message translates to:
  /// **'هذا الحقل مطلوب'**
  String get fieldRequired;

  /// No description provided for @universityIdInvalid.
  ///
  /// In ar, this message translates to:
  /// **'الرقم الجامعي يجب أن يكون 3 محارف على الأقل'**
  String get universityIdInvalid;

  /// No description provided for @networkUnreachable.
  ///
  /// In ar, this message translates to:
  /// **'تعذر الاتصال بالخادم؛ تحقق من الإنترنت وحاول مجدداً'**
  String get networkUnreachable;

  /// No description provided for @unexpectedError.
  ///
  /// In ar, this message translates to:
  /// **'حدث خطأ غير متوقع؛ أعد المحاولة'**
  String get unexpectedError;

  /// No description provided for @sessionExpired.
  ///
  /// In ar, this message translates to:
  /// **'انتهت الجلسة؛ يرجى تسجيل الدخول من جديد'**
  String get sessionExpired;

  /// No description provided for @homeTitle.
  ///
  /// In ar, this message translates to:
  /// **'الرئيسية'**
  String get homeTitle;

  /// No description provided for @homeTodayLectures.
  ///
  /// In ar, this message translates to:
  /// **'محاضرات اليوم'**
  String get homeTodayLectures;

  /// No description provided for @homeNoLectures.
  ///
  /// In ar, this message translates to:
  /// **'لا محاضرات اليوم'**
  String get homeNoLectures;

  /// No description provided for @homeLatestAnnouncement.
  ///
  /// In ar, this message translates to:
  /// **'آخر إعلان'**
  String get homeLatestAnnouncement;

  /// No description provided for @homeViewAll.
  ///
  /// In ar, this message translates to:
  /// **'عرض الكل'**
  String get homeViewAll;

  /// No description provided for @welcome.
  ///
  /// In ar, this message translates to:
  /// **'أهلاً'**
  String get welcome;

  /// No description provided for @logoutButton.
  ///
  /// In ar, this message translates to:
  /// **'تسجيل الخروج'**
  String get logoutButton;

  /// No description provided for @mustChangePasswordNotice.
  ///
  /// In ar, this message translates to:
  /// **'يُطلب منك تغيير كلمة المرور الأولية'**
  String get mustChangePasswordNotice;

  /// No description provided for @changePasswordTitle.
  ///
  /// In ar, this message translates to:
  /// **'تغيير كلمة المرور'**
  String get changePasswordTitle;

  /// No description provided for @changePasswordButton.
  ///
  /// In ar, this message translates to:
  /// **'حفظ كلمة المرور'**
  String get changePasswordButton;

  /// No description provided for @currentPasswordLabel.
  ///
  /// In ar, this message translates to:
  /// **'كلمة المرور الحالية'**
  String get currentPasswordLabel;

  /// No description provided for @newPasswordLabel.
  ///
  /// In ar, this message translates to:
  /// **'كلمة المرور الجديدة'**
  String get newPasswordLabel;

  /// No description provided for @passwordTooShort.
  ///
  /// In ar, this message translates to:
  /// **'كلمة المرور يجب ألا تقل عن 8 محارف'**
  String get passwordTooShort;

  /// No description provided for @passwordChanged.
  ///
  /// In ar, this message translates to:
  /// **'تم تغيير كلمة المرور؛ سجّل الدخول من جديد'**
  String get passwordChanged;

  /// No description provided for @departmentLabel.
  ///
  /// In ar, this message translates to:
  /// **'القسم'**
  String get departmentLabel;

  /// No description provided for @stageLabel.
  ///
  /// In ar, this message translates to:
  /// **'المرحلة'**
  String get stageLabel;

  /// No description provided for @groupLabel.
  ///
  /// In ar, this message translates to:
  /// **'الشعبة'**
  String get groupLabel;

  /// No description provided for @scanAttendanceCard.
  ///
  /// In ar, this message translates to:
  /// **'مسح الحضور'**
  String get scanAttendanceCard;

  /// No description provided for @scanAttendanceCardHint.
  ///
  /// In ar, this message translates to:
  /// **'امسح رمز الجلسة لتسجيل حضورك'**
  String get scanAttendanceCardHint;

  /// No description provided for @todaySessionsCard.
  ///
  /// In ar, this message translates to:
  /// **'حصص اليوم'**
  String get todaySessionsCard;

  /// No description provided for @todaySessionsCardHint.
  ///
  /// In ar, this message translates to:
  /// **'افتح الجلسة وتابع الحضور لحظياً'**
  String get todaySessionsCardHint;

  /// No description provided for @todaySessionsTitle.
  ///
  /// In ar, this message translates to:
  /// **'حصص اليوم'**
  String get todaySessionsTitle;

  /// No description provided for @noSessionsToday.
  ///
  /// In ar, this message translates to:
  /// **'لا توجد حصص مجدولة لك اليوم'**
  String get noSessionsToday;

  /// No description provided for @noStudentsInFilter.
  ///
  /// In ar, this message translates to:
  /// **'لا يوجد طلاب في هذه الحالة'**
  String get noStudentsInFilter;

  /// No description provided for @retryButton.
  ///
  /// In ar, this message translates to:
  /// **'إعادة المحاولة'**
  String get retryButton;

  /// No description provided for @scanTitle.
  ///
  /// In ar, this message translates to:
  /// **'مسح الحضور'**
  String get scanTitle;

  /// No description provided for @scannerHint.
  ///
  /// In ar, this message translates to:
  /// **'ضع رمز الجلسة داخل الإطار'**
  String get scannerHint;

  /// No description provided for @scanHelp.
  ///
  /// In ar, this message translates to:
  /// **'وجّه الكاميرا إلى رمز الجلسة المعروض عند التدريسي. يتجدد الرمز كل 20 ثانية.'**
  String get scanHelp;

  /// No description provided for @lastScanResult.
  ///
  /// In ar, this message translates to:
  /// **'نتيجة آخر مسح'**
  String get lastScanResult;

  /// No description provided for @presentStatus.
  ///
  /// In ar, this message translates to:
  /// **'حاضر'**
  String get presentStatus;

  /// No description provided for @lateStatus.
  ///
  /// In ar, this message translates to:
  /// **'متأخر'**
  String get lateStatus;

  /// No description provided for @absentStatus.
  ///
  /// In ar, this message translates to:
  /// **'غائب'**
  String get absentStatus;

  /// No description provided for @excusedStatus.
  ///
  /// In ar, this message translates to:
  /// **'غياب بعذر'**
  String get excusedStatus;

  /// No description provided for @flaggedStatus.
  ///
  /// In ar, this message translates to:
  /// **'مشكوك'**
  String get flaggedStatus;

  /// No description provided for @notRecordedStatus.
  ///
  /// In ar, this message translates to:
  /// **'لم يُسجّل'**
  String get notRecordedStatus;

  /// No description provided for @deviceNote.
  ///
  /// In ar, this message translates to:
  /// **'المسح مرتبط بجهازك المسجّل · لا يمكن المسح من جهاز آخر'**
  String get deviceNote;

  /// No description provided for @invalidQrError.
  ///
  /// In ar, this message translates to:
  /// **'الرمز الممسوح ليس رمز حضور صالحاً لهذا التطبيق'**
  String get invalidQrError;

  /// No description provided for @missingDeviceError.
  ///
  /// In ar, this message translates to:
  /// **'معلومات جهازك غير مكتملة؛ سجّل الدخول من جديد ثم أعد المحاولة'**
  String get missingDeviceError;

  /// No description provided for @flagNoLocation.
  ///
  /// In ar, this message translates to:
  /// **'لم يُرسَل موقع الجهاز مع المسح؛ سيراجع التدريسي الحضور'**
  String get flagNoLocation;

  /// No description provided for @flagOutsideCampus.
  ///
  /// In ar, this message translates to:
  /// **'الموقع خارج نطاق القاعة (نحو {meters}م)؛ سيراجع التدريسي الحضور'**
  String flagOutsideCampus(int meters);

  /// No description provided for @liveTitle.
  ///
  /// In ar, this message translates to:
  /// **'قائمة الحاضرين'**
  String get liveTitle;

  /// No description provided for @liveAttendance.
  ///
  /// In ar, this message translates to:
  /// **'الحضور اللحظي'**
  String get liveAttendance;

  /// No description provided for @qrRenewsChip.
  ///
  /// In ar, this message translates to:
  /// **'الرمز يتجدد تلقائياً'**
  String get qrRenewsChip;

  /// No description provided for @presentOfTotal.
  ///
  /// In ar, this message translates to:
  /// **'{present} حاضراً من {total}'**
  String presentOfTotal(int present, int total);

  /// No description provided for @percentValue.
  ///
  /// In ar, this message translates to:
  /// **'{percent}%'**
  String percentValue(int percent);

  /// No description provided for @lateCount.
  ///
  /// In ar, this message translates to:
  /// **'متأخر {count}'**
  String lateCount(int count);

  /// No description provided for @flaggedCount.
  ///
  /// In ar, this message translates to:
  /// **'مشكوك {count}'**
  String flaggedCount(int count);

  /// No description provided for @absentCount.
  ///
  /// In ar, this message translates to:
  /// **'غائب {count}'**
  String absentCount(int count);

  /// No description provided for @filterAll.
  ///
  /// In ar, this message translates to:
  /// **'الكل'**
  String get filterAll;

  /// No description provided for @sessionKindTheory.
  ///
  /// In ar, this message translates to:
  /// **'نظري'**
  String get sessionKindTheory;

  /// No description provided for @sessionKindLab.
  ///
  /// In ar, this message translates to:
  /// **'مختبر'**
  String get sessionKindLab;

  /// No description provided for @sessionStatusOpen.
  ///
  /// In ar, this message translates to:
  /// **'الجلسة مفتوحة'**
  String get sessionStatusOpen;

  /// No description provided for @sessionStatusClosed.
  ///
  /// In ar, this message translates to:
  /// **'أُغلقت الجلسة'**
  String get sessionStatusClosed;

  /// No description provided for @sessionStatusScheduled.
  ///
  /// In ar, this message translates to:
  /// **'لم تُفتح بعد'**
  String get sessionStatusScheduled;

  /// No description provided for @sessionStatusCancelled.
  ///
  /// In ar, this message translates to:
  /// **'ملغاة'**
  String get sessionStatusCancelled;

  /// No description provided for @openSessionButton.
  ///
  /// In ar, this message translates to:
  /// **'فتح الجلسة'**
  String get openSessionButton;

  /// No description provided for @openSessionHint.
  ///
  /// In ar, this message translates to:
  /// **'افتح الجلسة عند بدء المحاضرة ليبدأ استقبال المسح ويظهر الرمز للطلبة.'**
  String get openSessionHint;

  /// No description provided for @closeSessionButton.
  ///
  /// In ar, this message translates to:
  /// **'إغلاق الجلسة'**
  String get closeSessionButton;

  /// No description provided for @closeSessionNote.
  ///
  /// In ar, this message translates to:
  /// **'إغلاق الجلسة يوقف استقبال المسح فوراً.'**
  String get closeSessionNote;

  /// No description provided for @closeSessionConfirmTitle.
  ///
  /// In ar, this message translates to:
  /// **'إغلاق الجلسة؟'**
  String get closeSessionConfirmTitle;

  /// No description provided for @closeSessionConfirmBody.
  ///
  /// In ar, this message translates to:
  /// **'سيُسجَّل غياب من لم يسجّل حضوره، ويتوقف استقبال المسح فوراً.'**
  String get closeSessionConfirmBody;

  /// No description provided for @confirmButton.
  ///
  /// In ar, this message translates to:
  /// **'تأكيد'**
  String get confirmButton;

  /// No description provided for @cancelButton.
  ///
  /// In ar, this message translates to:
  /// **'إلغاء'**
  String get cancelButton;

  /// No description provided for @absentMarkedNote.
  ///
  /// In ar, this message translates to:
  /// **'سُجّل غياب {count} طالباً لم يسجّلوا حضورهم.'**
  String absentMarkedNote(int count);

  /// No description provided for @timetableTitle.
  ///
  /// In ar, this message translates to:
  /// **'الجدول الأسبوعي'**
  String get timetableTitle;

  /// No description provided for @timetableEmpty.
  ///
  /// In ar, this message translates to:
  /// **'لا توجد محاضرات في هذه الفترة'**
  String get timetableEmpty;

  /// No description provided for @timetableOffline.
  ///
  /// In ar, this message translates to:
  /// **'تعذر الاتصال؛ تُعرض بيانات محفوظة من {time}'**
  String timetableOffline(String time);

  /// No description provided for @changeCancelled.
  ///
  /// In ar, this message translates to:
  /// **'ملغاة'**
  String get changeCancelled;

  /// No description provided for @changeMoved.
  ///
  /// In ar, this message translates to:
  /// **'نُقلت'**
  String get changeMoved;

  /// No description provided for @changeExtra.
  ///
  /// In ar, this message translates to:
  /// **'إضافة'**
  String get changeExtra;

  /// No description provided for @weekdaySunday.
  ///
  /// In ar, this message translates to:
  /// **'الأحد'**
  String get weekdaySunday;

  /// No description provided for @weekdayMonday.
  ///
  /// In ar, this message translates to:
  /// **'الاثنين'**
  String get weekdayMonday;

  /// No description provided for @weekdayTuesday.
  ///
  /// In ar, this message translates to:
  /// **'الثلاثاء'**
  String get weekdayTuesday;

  /// No description provided for @weekdayWednesday.
  ///
  /// In ar, this message translates to:
  /// **'الأربعاء'**
  String get weekdayWednesday;

  /// No description provided for @weekdayThursday.
  ///
  /// In ar, this message translates to:
  /// **'الخميس'**
  String get weekdayThursday;

  /// No description provided for @weekdayFriday.
  ///
  /// In ar, this message translates to:
  /// **'الجمعة'**
  String get weekdayFriday;

  /// No description provided for @weekdaySaturday.
  ///
  /// In ar, this message translates to:
  /// **'السبت'**
  String get weekdaySaturday;

  /// No description provided for @courseMaterialsTitle.
  ///
  /// In ar, this message translates to:
  /// **'مواد المقررات'**
  String get courseMaterialsTitle;

  /// No description provided for @noOfferings.
  ///
  /// In ar, this message translates to:
  /// **'لا توجد مواد دراسية مسجَّلة'**
  String get noOfferings;

  /// No description provided for @courseMaterialsEmpty.
  ///
  /// In ar, this message translates to:
  /// **'لا مواد منشورة بعد'**
  String get courseMaterialsEmpty;

  /// No description provided for @materialsDownload.
  ///
  /// In ar, this message translates to:
  /// **'تنزيل'**
  String get materialsDownload;

  /// No description provided for @materialsOpenLink.
  ///
  /// In ar, this message translates to:
  /// **'فتح'**
  String get materialsOpenLink;

  /// No description provided for @materialsLinkOpenFailed.
  ///
  /// In ar, this message translates to:
  /// **'تعذر فتح الرابط؛ حاول مجدداً'**
  String get materialsLinkOpenFailed;

  /// No description provided for @materialsWeek.
  ///
  /// In ar, this message translates to:
  /// **'الأسبوع {week}'**
  String materialsWeek(int week);

  /// No description provided for @gradesTitle.
  ///
  /// In ar, this message translates to:
  /// **'درجاتك'**
  String get gradesTitle;

  /// No description provided for @gradesEmpty.
  ///
  /// In ar, this message translates to:
  /// **'لا درجات منشورة بعد'**
  String get gradesEmpty;

  /// No description provided for @notGradedYet.
  ///
  /// In ar, this message translates to:
  /// **'لم تُرصد'**
  String get notGradedYet;

  /// No description provided for @weightedOfTotal.
  ///
  /// In ar, this message translates to:
  /// **'{total} من {sum}'**
  String weightedOfTotal(String total, String sum);

  /// No description provided for @scoreOfMax.
  ///
  /// In ar, this message translates to:
  /// **'{score} / {max}'**
  String scoreOfMax(String score, String max);

  /// No description provided for @weightShort.
  ///
  /// In ar, this message translates to:
  /// **'وزن {weight}%'**
  String weightShort(String weight);

  /// No description provided for @timetableCard.
  ///
  /// In ar, this message translates to:
  /// **'الجدول'**
  String get timetableCard;

  /// No description provided for @timetableCardHint.
  ///
  /// In ar, this message translates to:
  /// **'محاضراتك وتغييراتها المؤرخة'**
  String get timetableCardHint;

  /// No description provided for @materialsCardHint.
  ///
  /// In ar, this message translates to:
  /// **'ملفات المحاضرات وروابطها'**
  String get materialsCardHint;

  /// No description provided for @gradesCardHint.
  ///
  /// In ar, this message translates to:
  /// **'نتائجك المنشورة والمجموع الموزون'**
  String get gradesCardHint;

  /// No description provided for @gradeEntryTitle.
  ///
  /// In ar, this message translates to:
  /// **'إدخال الدرجات'**
  String get gradeEntryTitle;

  /// No description provided for @gradeEntryHint.
  ///
  /// In ar, this message translates to:
  /// **'أدخل درجات التقييم كمسودة، والنشر يتم بموافقة الكلية'**
  String get gradeEntryHint;

  /// No description provided for @chooseOfferingLabel.
  ///
  /// In ar, this message translates to:
  /// **'المادة'**
  String get chooseOfferingLabel;

  /// No description provided for @chooseAssessmentLabel.
  ///
  /// In ar, this message translates to:
  /// **'التقييم'**
  String get chooseAssessmentLabel;

  /// No description provided for @noAssessmentsYet.
  ///
  /// In ar, this message translates to:
  /// **'لا تقييمات بعد — أنشئ تقييماً أولاً'**
  String get noAssessmentsYet;

  /// No description provided for @newAssessmentButton.
  ///
  /// In ar, this message translates to:
  /// **'تقييم جديد'**
  String get newAssessmentButton;

  /// No description provided for @assessmentNameLabel.
  ///
  /// In ar, this message translates to:
  /// **'اسم التقييم'**
  String get assessmentNameLabel;

  /// No description provided for @assessmentKindLabel.
  ///
  /// In ar, this message translates to:
  /// **'النوع'**
  String get assessmentKindLabel;

  /// No description provided for @maxScoreLabel.
  ///
  /// In ar, this message translates to:
  /// **'الدرجة العظمى'**
  String get maxScoreLabel;

  /// No description provided for @weightPercentLabel.
  ///
  /// In ar, this message translates to:
  /// **'الوزن %'**
  String get weightPercentLabel;

  /// No description provided for @createAssessmentButton.
  ///
  /// In ar, this message translates to:
  /// **'إنشاء التقييم'**
  String get createAssessmentButton;

  /// No description provided for @assessmentCreated.
  ///
  /// In ar, this message translates to:
  /// **'أُنشئ التقييم'**
  String get assessmentCreated;

  /// No description provided for @gradedOfTotal.
  ///
  /// In ar, this message translates to:
  /// **'أُدخلت {graded} من {total} درجة'**
  String gradedOfTotal(int graded, int total);

  /// No description provided for @saveDraftButton.
  ///
  /// In ar, this message translates to:
  /// **'حفظ كمسودة'**
  String get saveDraftButton;

  /// No description provided for @draftSaved.
  ///
  /// In ar, this message translates to:
  /// **'حُفظت المسودة'**
  String get draftSaved;

  /// No description provided for @publishGradesButton.
  ///
  /// In ar, this message translates to:
  /// **'نشر الدرجات'**
  String get publishGradesButton;

  /// No description provided for @publishNeedsAdmin.
  ///
  /// In ar, this message translates to:
  /// **'النشر يتطلب موافقة مدير الكلية'**
  String get publishNeedsAdmin;

  /// No description provided for @publishedSuccess.
  ///
  /// In ar, this message translates to:
  /// **'نُشرت الدرجات وأُشعر {count} طالباً'**
  String publishedSuccess(int count);

  /// No description provided for @scoreRangeError.
  ///
  /// In ar, this message translates to:
  /// **'الدرجة يجب أن تكون بين 0 و{max}'**
  String scoreRangeError(String max);

  /// No description provided for @assessmentLocked.
  ///
  /// In ar, this message translates to:
  /// **'التقييم منشور — لا يمكن تعديل درجاته'**
  String get assessmentLocked;

  /// No description provided for @assessmentPublished.
  ///
  /// In ar, this message translates to:
  /// **'منشور'**
  String get assessmentPublished;

  /// No description provided for @kindQuiz.
  ///
  /// In ar, this message translates to:
  /// **'كوز'**
  String get kindQuiz;

  /// No description provided for @kindLab.
  ///
  /// In ar, this message translates to:
  /// **'مختبر'**
  String get kindLab;

  /// No description provided for @kindMidterm.
  ///
  /// In ar, this message translates to:
  /// **'نصفي'**
  String get kindMidterm;

  /// No description provided for @kindFinal.
  ///
  /// In ar, this message translates to:
  /// **'نهائي'**
  String get kindFinal;

  /// No description provided for @kindOther.
  ///
  /// In ar, this message translates to:
  /// **'أخرى'**
  String get kindOther;

  /// No description provided for @assessmentWeightHint.
  ///
  /// In ar, this message translates to:
  /// **'مجموع أوزان التقييمات لا يتجاوز 100%'**
  String get assessmentWeightHint;

  /// No description provided for @loginTotpLabel.
  ///
  /// In ar, this message translates to:
  /// **'رمز التحقق بخطوتين'**
  String get loginTotpLabel;

  /// No description provided for @loginTotpHint.
  ///
  /// In ar, this message translates to:
  /// **'أدخل الرمز من تطبيق المصادقة (يتطلبه حساب التدريسي/الإدارة)'**
  String get loginTotpHint;

  /// No description provided for @totpRequiredError.
  ///
  /// In ar, this message translates to:
  /// **'هذا الحساب محمي بالتحقق بخطوتين؛ أدخل الرمز ثم أعد المحاولة'**
  String get totpRequiredError;

  /// No description provided for @totpInvalidError.
  ///
  /// In ar, this message translates to:
  /// **'رمز التحقق غير صحيح أو انتهت صلاحيته'**
  String get totpInvalidError;

  /// No description provided for @announcementsCard.
  ///
  /// In ar, this message translates to:
  /// **'الإعلانات'**
  String get announcementsCard;

  /// No description provided for @announcementsCardHint.
  ///
  /// In ar, this message translates to:
  /// **'أخبار الكلية وقسمك وموادك'**
  String get announcementsCardHint;

  /// No description provided for @announcementsTitle.
  ///
  /// In ar, this message translates to:
  /// **'الإعلانات'**
  String get announcementsTitle;

  /// No description provided for @announcementsEmpty.
  ///
  /// In ar, this message translates to:
  /// **'لا إعلانات منشورة حالياً'**
  String get announcementsEmpty;

  /// No description provided for @announcementPinned.
  ///
  /// In ar, this message translates to:
  /// **'مثبَّت'**
  String get announcementPinned;

  /// No description provided for @announcementPriorityHigh.
  ///
  /// In ar, this message translates to:
  /// **'مهم'**
  String get announcementPriorityHigh;

  /// No description provided for @announcementMarkedRead.
  ///
  /// In ar, this message translates to:
  /// **'تم تعليم الإعلان كمقروء'**
  String get announcementMarkedRead;

  /// No description provided for @announcementUnknownScope.
  ///
  /// In ar, this message translates to:
  /// **'إعلان'**
  String get announcementUnknownScope;

  /// No description provided for @inboxCard.
  ///
  /// In ar, this message translates to:
  /// **'الإشعارات'**
  String get inboxCard;

  /// No description provided for @inboxCardHint.
  ///
  /// In ar, this message translates to:
  /// **'صندوق الوارد وتنبيهات الأجهزة'**
  String get inboxCardHint;

  /// No description provided for @inboxTitle.
  ///
  /// In ar, this message translates to:
  /// **'الإشعارات'**
  String get inboxTitle;

  /// No description provided for @inboxEmpty.
  ///
  /// In ar, this message translates to:
  /// **'لا إشعارات بعد'**
  String get inboxEmpty;

  /// No description provided for @markAllRead.
  ///
  /// In ar, this message translates to:
  /// **'تعليم الكل كمقروء'**
  String get markAllRead;

  /// No description provided for @unreadBadge.
  ///
  /// In ar, this message translates to:
  /// **'{count} جديد'**
  String unreadBadge(int count);

  /// No description provided for @notificationsPermissionDenied.
  ///
  /// In ar, this message translates to:
  /// **'لم يُمنح إذن الإشعارات؛ يمكنك متابعتها داخل التطبيق'**
  String get notificationsPermissionDenied;

  /// No description provided for @notificationsEnabledMessage.
  ///
  /// In ar, this message translates to:
  /// **'تم تفعيل إشعارات المحاضرات على هذا الجهاز'**
  String get notificationsEnabledMessage;

  /// No description provided for @reminderLectureTitle.
  ///
  /// In ar, this message translates to:
  /// **'محاضرة بعد 15 دقيقة'**
  String get reminderLectureTitle;

  /// No description provided for @reminderLectureBody.
  ///
  /// In ar, this message translates to:
  /// **'{course} — {room} الساعة {time}'**
  String reminderLectureBody(String course, String room, String time);

  /// No description provided for @reminderDigestTitle.
  ///
  /// In ar, this message translates to:
  /// **'محاضرات الغد'**
  String get reminderDigestTitle;

  /// No description provided for @reminderDigestBody.
  ///
  /// In ar, this message translates to:
  /// **'{count} محاضرة تبدأ الساعة {time}'**
  String reminderDigestBody(int count, String time);

  /// No description provided for @reminderDigestEmpty.
  ///
  /// In ar, this message translates to:
  /// **'لا محاضرات غداً'**
  String get reminderDigestEmpty;

  /// No description provided for @reminderChannelName.
  ///
  /// In ar, this message translates to:
  /// **'تذكيرات المحاضرات'**
  String get reminderChannelName;

  /// No description provided for @reminderChannelDescription.
  ///
  /// In ar, this message translates to:
  /// **'تذكير قبل المحاضرة وملخص محاضرات الغد'**
  String get reminderChannelDescription;

  /// No description provided for @excusesCard.
  ///
  /// In ar, this message translates to:
  /// **'الأعذار'**
  String get excusesCard;

  /// No description provided for @excusesCardHint.
  ///
  /// In ar, this message translates to:
  /// **'رفع عذر غياب ومتابعة قراره'**
  String get excusesCardHint;

  /// No description provided for @excusesTitle.
  ///
  /// In ar, this message translates to:
  /// **'أعذاري'**
  String get excusesTitle;

  /// No description provided for @excusesEmpty.
  ///
  /// In ar, this message translates to:
  /// **'لا أعذار مرفوعة'**
  String get excusesEmpty;

  /// No description provided for @excuseNewTitle.
  ///
  /// In ar, this message translates to:
  /// **'عذر غياب جديد'**
  String get excuseNewTitle;

  /// No description provided for @excuseSessionLabel.
  ///
  /// In ar, this message translates to:
  /// **'المحاضرة'**
  String get excuseSessionLabel;

  /// No description provided for @excuseSelectSession.
  ///
  /// In ar, this message translates to:
  /// **'اختر المحاضرة الغائبة'**
  String get excuseSelectSession;

  /// No description provided for @excuseNoSessions.
  ///
  /// In ar, this message translates to:
  /// **'لا محاضرات مؤهلة لرفع عذر (لا غياب خلال 14 يوماً)'**
  String get excuseNoSessions;

  /// No description provided for @excuseReasonLabel.
  ///
  /// In ar, this message translates to:
  /// **'سبب الغياب'**
  String get excuseReasonLabel;

  /// No description provided for @excuseReasonHint.
  ///
  /// In ar, this message translates to:
  /// **'اشرح السبب بإيجاز، وأرفق صورة التقرير إن وُجد'**
  String get excuseReasonHint;

  /// No description provided for @excuseAttach.
  ///
  /// In ar, this message translates to:
  /// **'إرفاق صورة أو PDF'**
  String get excuseAttach;

  /// No description provided for @excuseAttachCamera.
  ///
  /// In ar, this message translates to:
  /// **'التقاط صورة'**
  String get excuseAttachCamera;

  /// No description provided for @excuseAttachGallery.
  ///
  /// In ar, this message translates to:
  /// **'من المعرض'**
  String get excuseAttachGallery;

  /// No description provided for @excuseAttachmentChosen.
  ///
  /// In ar, this message translates to:
  /// **'تم اختيار المرفق'**
  String get excuseAttachmentChosen;

  /// No description provided for @excuseSubmit.
  ///
  /// In ar, this message translates to:
  /// **'إرسال العذر'**
  String get excuseSubmit;

  /// No description provided for @excuseSubmitted.
  ///
  /// In ar, this message translates to:
  /// **'أُرسل العذر للمراجعة'**
  String get excuseSubmitted;

  /// No description provided for @excuseStatusPending.
  ///
  /// In ar, this message translates to:
  /// **'قيد المراجعة'**
  String get excuseStatusPending;

  /// No description provided for @excuseStatusApproved.
  ///
  /// In ar, this message translates to:
  /// **'مقبول'**
  String get excuseStatusApproved;

  /// No description provided for @excuseStatusRejected.
  ///
  /// In ar, this message translates to:
  /// **'مرفوض'**
  String get excuseStatusRejected;

  /// No description provided for @excuseReviewNote.
  ///
  /// In ar, this message translates to:
  /// **'ملاحظة المراجع'**
  String get excuseReviewNote;

  /// No description provided for @excuseWithdraw.
  ///
  /// In ar, this message translates to:
  /// **'سحب العذر'**
  String get excuseWithdraw;

  /// No description provided for @excuseWithdrawn.
  ///
  /// In ar, this message translates to:
  /// **'تم سحب العذر'**
  String get excuseWithdrawn;

  /// No description provided for @excuseWindowClosed.
  ///
  /// In ar, this message translates to:
  /// **'انتهت مدة رفع العذر لهذه المحاضرة (14 يوماً)'**
  String get excuseWindowClosed;

  /// No description provided for @excuseReviewTitle.
  ///
  /// In ar, this message translates to:
  /// **'مراجعة الأعذار'**
  String get excuseReviewTitle;

  /// No description provided for @excuseReviewEmpty.
  ///
  /// In ar, this message translates to:
  /// **'لا أعذار تنتظر المراجعة'**
  String get excuseReviewEmpty;

  /// No description provided for @excuseApprove.
  ///
  /// In ar, this message translates to:
  /// **'قبول'**
  String get excuseApprove;

  /// No description provided for @excuseReject.
  ///
  /// In ar, this message translates to:
  /// **'رفض'**
  String get excuseReject;

  /// No description provided for @excuseReviewNoteHint.
  ///
  /// In ar, this message translates to:
  /// **'ملاحظة تظهر للطالب (اختياري)'**
  String get excuseReviewNoteHint;

  /// No description provided for @excuseReviewed.
  ///
  /// In ar, this message translates to:
  /// **'تم تسجيل القرار'**
  String get excuseReviewed;

  /// No description provided for @excusePendingCount.
  ///
  /// In ar, this message translates to:
  /// **'بانتظار المراجعة: {count}'**
  String excusePendingCount(int count);

  /// No description provided for @requestsCard.
  ///
  /// In ar, this message translates to:
  /// **'الطلبات'**
  String get requestsCard;

  /// No description provided for @requestsCardHint.
  ///
  /// In ar, this message translates to:
  /// **'تواصل مع قسمك بشأن دراستك'**
  String get requestsCardHint;

  /// No description provided for @requestsTitle.
  ///
  /// In ar, this message translates to:
  /// **'طلباتي'**
  String get requestsTitle;

  /// No description provided for @requestsEmpty.
  ///
  /// In ar, this message translates to:
  /// **'لا طلبات بعد'**
  String get requestsEmpty;

  /// No description provided for @requestNewTitle.
  ///
  /// In ar, this message translates to:
  /// **'طلب جديد'**
  String get requestNewTitle;

  /// No description provided for @requestCategoryLabel.
  ///
  /// In ar, this message translates to:
  /// **'التصنيف'**
  String get requestCategoryLabel;

  /// No description provided for @requestCategoryAcademic.
  ///
  /// In ar, this message translates to:
  /// **'مسألة أكاديمية'**
  String get requestCategoryAcademic;

  /// No description provided for @requestCategorySchedule.
  ///
  /// In ar, this message translates to:
  /// **'الجدول والقاعات'**
  String get requestCategorySchedule;

  /// No description provided for @requestCategoryGrades.
  ///
  /// In ar, this message translates to:
  /// **'درجة أو تقييم'**
  String get requestCategoryGrades;

  /// No description provided for @requestCategoryDocuments.
  ///
  /// In ar, this message translates to:
  /// **'وثيقة أو تأييد'**
  String get requestCategoryDocuments;

  /// No description provided for @requestCategoryOther.
  ///
  /// In ar, this message translates to:
  /// **'أخرى'**
  String get requestCategoryOther;

  /// No description provided for @requestSubjectLabel.
  ///
  /// In ar, this message translates to:
  /// **'الموضوع'**
  String get requestSubjectLabel;

  /// No description provided for @requestBodyLabel.
  ///
  /// In ar, this message translates to:
  /// **'تفاصيل الطلب'**
  String get requestBodyLabel;

  /// No description provided for @requestSend.
  ///
  /// In ar, this message translates to:
  /// **'إرسال الطلب'**
  String get requestSend;

  /// No description provided for @requestCreated.
  ///
  /// In ar, this message translates to:
  /// **'أُرسل طلبك إلى قسمك'**
  String get requestCreated;

  /// No description provided for @requestDetailTitle.
  ///
  /// In ar, this message translates to:
  /// **'تفاصيل الطلب'**
  String get requestDetailTitle;

  /// No description provided for @requestReplyHint.
  ///
  /// In ar, this message translates to:
  /// **'اكتب رسالتك…'**
  String get requestReplyHint;

  /// No description provided for @requestSendReply.
  ///
  /// In ar, this message translates to:
  /// **'إرسال'**
  String get requestSendReply;

  /// No description provided for @requestClosedNotice.
  ///
  /// In ar, this message translates to:
  /// **'الطلب مغلق؛ لا يمكن إضافة رسائل'**
  String get requestClosedNotice;

  /// No description provided for @requestStatusOpen.
  ///
  /// In ar, this message translates to:
  /// **'مفتوح'**
  String get requestStatusOpen;

  /// No description provided for @requestStatusInProgress.
  ///
  /// In ar, this message translates to:
  /// **'قيد المعالجة'**
  String get requestStatusInProgress;

  /// No description provided for @requestStatusResolved.
  ///
  /// In ar, this message translates to:
  /// **'تم الحل'**
  String get requestStatusResolved;

  /// No description provided for @requestStatusClosed.
  ///
  /// In ar, this message translates to:
  /// **'مغلق'**
  String get requestStatusClosed;

  /// No description provided for @conversationEmpty.
  ///
  /// In ar, this message translates to:
  /// **'لا رسائل بعد'**
  String get conversationEmpty;

  /// No description provided for @identityCard.
  ///
  /// In ar, this message translates to:
  /// **'الهوية الرقمية'**
  String get identityCard;

  /// No description provided for @identityCardHint.
  ///
  /// In ar, this message translates to:
  /// **'بطاقة QR موقّعة تُثبت هويتك في الامتحان'**
  String get identityCardHint;

  /// No description provided for @identityTitle.
  ///
  /// In ar, this message translates to:
  /// **'بطاقتك الرقمية'**
  String get identityTitle;

  /// No description provided for @identityCardNote.
  ///
  /// In ar, this message translates to:
  /// **'اعرض البطاقة للتدريسي أو بوابة القاعة. تتجدد تلقائياً ولا تعمل لقطة الشاشة القديمة.'**
  String get identityCardNote;

  /// No description provided for @identityValidFor.
  ///
  /// In ar, this message translates to:
  /// **'صالحة {seconds} ثانية'**
  String identityValidFor(int seconds);

  /// No description provided for @identityRefreshButton.
  ///
  /// In ar, this message translates to:
  /// **'تحديث البطاقة'**
  String get identityRefreshButton;

  /// No description provided for @identityVerifyTitle.
  ///
  /// In ar, this message translates to:
  /// **'التحقق من بطاقة طالب'**
  String get identityVerifyTitle;

  /// No description provided for @identityVerifyHint.
  ///
  /// In ar, this message translates to:
  /// **'وجّه الكاميرا إلى بطاقة الطالب الرقمية'**
  String get identityVerifyHint;

  /// No description provided for @identityVerifyButton.
  ///
  /// In ar, this message translates to:
  /// **'تحقق'**
  String get identityVerifyButton;

  /// No description provided for @identityValidTitle.
  ///
  /// In ar, this message translates to:
  /// **'بطاقة صالحة'**
  String get identityValidTitle;

  /// No description provided for @identityInvalidTitle.
  ///
  /// In ar, this message translates to:
  /// **'بطاقة غير صالحة'**
  String get identityInvalidTitle;

  /// No description provided for @identityStudentLabel.
  ///
  /// In ar, this message translates to:
  /// **'الطالب'**
  String get identityStudentLabel;

  /// No description provided for @identityStudyTypeMorning.
  ///
  /// In ar, this message translates to:
  /// **'صباحي'**
  String get identityStudyTypeMorning;

  /// No description provided for @identityStudyTypeEvening.
  ///
  /// In ar, this message translates to:
  /// **'مسائي'**
  String get identityStudyTypeEvening;

  /// No description provided for @identityCardForStaffOnly.
  ///
  /// In ar, this message translates to:
  /// **'التحقق من البطاقات متاح للتدريسي والإدارة'**
  String get identityCardForStaffOnly;

  /// No description provided for @identityExpiredError.
  ///
  /// In ar, this message translates to:
  /// **'انتهت صلاحية البطاقة؛ اطلب من الطالب تحديثها'**
  String get identityExpiredError;

  /// No description provided for @settingsCard.
  ///
  /// In ar, this message translates to:
  /// **'الإعدادات'**
  String get settingsCard;

  /// No description provided for @settingsCardHint.
  ///
  /// In ar, this message translates to:
  /// **'المظهر واللغة والتحقق بخطوتين'**
  String get settingsCardHint;

  /// No description provided for @settingsTitle.
  ///
  /// In ar, this message translates to:
  /// **'الإعدادات'**
  String get settingsTitle;

  /// No description provided for @settingsAppearance.
  ///
  /// In ar, this message translates to:
  /// **'المظهر'**
  String get settingsAppearance;

  /// No description provided for @settingsThemeLight.
  ///
  /// In ar, this message translates to:
  /// **'فاتح'**
  String get settingsThemeLight;

  /// No description provided for @settingsThemeDark.
  ///
  /// In ar, this message translates to:
  /// **'داكن'**
  String get settingsThemeDark;

  /// No description provided for @settingsThemeSystem.
  ///
  /// In ar, this message translates to:
  /// **'حسب النظام'**
  String get settingsThemeSystem;

  /// No description provided for @settingsLanguage.
  ///
  /// In ar, this message translates to:
  /// **'اللغة'**
  String get settingsLanguage;

  /// No description provided for @settingsLanguageArabic.
  ///
  /// In ar, this message translates to:
  /// **'العربية'**
  String get settingsLanguageArabic;

  /// No description provided for @settingsLanguageEnglish.
  ///
  /// In ar, this message translates to:
  /// **'English'**
  String get settingsLanguageEnglish;

  /// No description provided for @settingsSaved.
  ///
  /// In ar, this message translates to:
  /// **'تم حفظ الإعدادات'**
  String get settingsSaved;

  /// No description provided for @settingsNotifications.
  ///
  /// In ar, this message translates to:
  /// **'إشعارات المحاضرات'**
  String get settingsNotifications;

  /// No description provided for @settingsNotificationsHint.
  ///
  /// In ar, this message translates to:
  /// **'تذكير قبل 15 دقيقة وملخص محاضرات الغد'**
  String get settingsNotificationsHint;

  /// No description provided for @settingsNotificationsOn.
  ///
  /// In ar, this message translates to:
  /// **'مفعّلة على هذا الجهاز'**
  String get settingsNotificationsOn;

  /// No description provided for @settingsNotificationsOff.
  ///
  /// In ar, this message translates to:
  /// **'غير مفعّلة'**
  String get settingsNotificationsOff;

  /// No description provided for @enableNotificationsButton.
  ///
  /// In ar, this message translates to:
  /// **'تفعيل الإشعارات'**
  String get enableNotificationsButton;

  /// No description provided for @twoFactorTitle.
  ///
  /// In ar, this message translates to:
  /// **'التحقق بخطوتين'**
  String get twoFactorTitle;

  /// No description provided for @twoFactorHint.
  ///
  /// In ar, this message translates to:
  /// **'حماية إضافية لحساب التدريسي والإدارة عبر تطبيق مصادقة'**
  String get twoFactorHint;

  /// No description provided for @twoFactorEnabled.
  ///
  /// In ar, this message translates to:
  /// **'مفعّل'**
  String get twoFactorEnabled;

  /// No description provided for @twoFactorDisabled.
  ///
  /// In ar, this message translates to:
  /// **'غير مفعّل'**
  String get twoFactorDisabled;

  /// No description provided for @twoFactorSetup.
  ///
  /// In ar, this message translates to:
  /// **'بدء الإعداد'**
  String get twoFactorSetup;

  /// No description provided for @twoFactorSecretLabel.
  ///
  /// In ar, this message translates to:
  /// **'السرّ (أدخله يدوياً إن لم يقرأ الرمز)'**
  String get twoFactorSecretLabel;

  /// No description provided for @twoFactorCodeLabel.
  ///
  /// In ar, this message translates to:
  /// **'رمز التطبيق (6 أرقام)'**
  String get twoFactorCodeLabel;

  /// No description provided for @twoFactorEnable.
  ///
  /// In ar, this message translates to:
  /// **'تفعيل'**
  String get twoFactorEnable;

  /// No description provided for @twoFactorDisable.
  ///
  /// In ar, this message translates to:
  /// **'تعطيل'**
  String get twoFactorDisable;

  /// No description provided for @twoFactorPasswordLabel.
  ///
  /// In ar, this message translates to:
  /// **'كلمة المرور لتأكيد التعطيل'**
  String get twoFactorPasswordLabel;

  /// No description provided for @twoFactorEnabledMessage.
  ///
  /// In ar, this message translates to:
  /// **'تم تفعيل التحقق بخطوتين'**
  String get twoFactorEnabledMessage;

  /// No description provided for @twoFactorDisabledMessage.
  ///
  /// In ar, this message translates to:
  /// **'تم تعطيل التحقق بخطوتين'**
  String get twoFactorDisabledMessage;

  /// No description provided for @twoFactorNotAvailable.
  ///
  /// In ar, this message translates to:
  /// **'متاح لحساب التدريسي والإدارة فقط'**
  String get twoFactorNotAvailable;

  /// No description provided for @twoFactorSetupHint.
  ///
  /// In ar, this message translates to:
  /// **'أضف السرّ إلى تطبيق Google Authenticator أو أي تطبيق TOTP ثم أدخل الرمز الظاهر.'**
  String get twoFactorSetupHint;

  /// No description provided for @dataFromCache.
  ///
  /// In ar, this message translates to:
  /// **'تعذر الاتصال؛ تُعرض بيانات محفوظة من {time}'**
  String dataFromCache(String time);

  /// No description provided for @offlineSavedHint.
  ///
  /// In ar, this message translates to:
  /// **'تُحدَّث البيانات تلقائياً عند عودة الاتصال'**
  String get offlineSavedHint;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['ar', 'en'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'ar':
      return AppLocalizationsAr();
    case 'en':
      return AppLocalizationsEn();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
