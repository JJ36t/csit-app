import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_ar.dart';

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
  static const List<Locale> supportedLocales = <Locale>[Locale('ar')];

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
      <String>['ar'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'ar':
      return AppLocalizationsAr();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
