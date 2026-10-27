// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Computer Science';

  @override
  String get collegeName =>
      'College of Computer Science and Information Technology — University of Al-Qadisiyah';

  @override
  String get loginTitle => 'Sign in';

  @override
  String get loginSubtitle =>
      'Use the university ID and password provided by your department';

  @override
  String get universityIdLabel => 'University ID';

  @override
  String get passwordLabel => 'Password';

  @override
  String get loginButton => 'Sign in';

  @override
  String get fieldRequired => 'This field is required';

  @override
  String get universityIdInvalid =>
      'University ID must be at least 3 characters';

  @override
  String get networkUnreachable =>
      'Cannot reach the server; check your connection and try again';

  @override
  String get unexpectedError => 'Something went wrong; please try again';

  @override
  String get sessionExpired => 'Session expired; please sign in again';

  @override
  String get homeTitle => 'Home';

  @override
  String get homeTodayLectures => 'Today\'s lectures';

  @override
  String get homeNoLectures => 'No lectures today';

  @override
  String get homeLatestAnnouncement => 'Latest announcement';

  @override
  String get homeViewAll => 'View all';

  @override
  String get welcome => 'Welcome';

  @override
  String get logoutButton => 'Sign out';

  @override
  String get mustChangePasswordNotice =>
      'You must change your initial password';

  @override
  String get changePasswordTitle => 'Change password';

  @override
  String get changePasswordButton => 'Save password';

  @override
  String get currentPasswordLabel => 'Current password';

  @override
  String get newPasswordLabel => 'New password';

  @override
  String get passwordTooShort => 'Password must be at least 8 characters';

  @override
  String get passwordChanged => 'Password changed; please sign in again';

  @override
  String get departmentLabel => 'Department';

  @override
  String get stageLabel => 'Stage';

  @override
  String get groupLabel => 'Section';

  @override
  String get scanAttendanceCard => 'Scan attendance';

  @override
  String get scanAttendanceCardHint =>
      'Scan the session code to record your attendance';

  @override
  String get todaySessionsCard => 'Today\'s lectures';

  @override
  String get todaySessionsCardHint =>
      'Open the session and follow attendance live';

  @override
  String get todaySessionsTitle => 'Today\'s lectures';

  @override
  String get noSessionsToday => 'No lectures scheduled for you today';

  @override
  String get noStudentsInFilter => 'No students in this state';

  @override
  String get retryButton => 'Retry';

  @override
  String get scanTitle => 'Scan attendance';

  @override
  String get scannerHint => 'Place the session code inside the frame';

  @override
  String get scanHelp =>
      'Point the camera at the code shown by your instructor. The code renews every 20 seconds.';

  @override
  String get lastScanResult => 'Last scan result';

  @override
  String get presentStatus => 'Present';

  @override
  String get lateStatus => 'Late';

  @override
  String get absentStatus => 'Absent';

  @override
  String get excusedStatus => 'Excused';

  @override
  String get flaggedStatus => 'Flagged';

  @override
  String get notRecordedStatus => 'Not recorded';

  @override
  String get deviceNote =>
      'Scanning is tied to your registered device — it cannot be done from another device';

  @override
  String get invalidQrError =>
      'The scanned code is not a valid attendance code for this app';

  @override
  String get missingDeviceError =>
      'Device information is incomplete; sign in again and retry';

  @override
  String get flagNoLocation =>
      'Location was not sent with the scan; your instructor will review it';

  @override
  String flagOutsideCampus(int meters) {
    return 'Location is outside the room range (about $meters m); your instructor will review it';
  }

  @override
  String get liveTitle => 'Attendance list';

  @override
  String get liveAttendance => 'Live attendance';

  @override
  String get qrRenewsChip => 'The code renews automatically';

  @override
  String presentOfTotal(int present, int total) {
    return '$present present of $total';
  }

  @override
  String percentValue(int percent) {
    return '$percent%';
  }

  @override
  String lateCount(int count) {
    return 'Late $count';
  }

  @override
  String flaggedCount(int count) {
    return 'Flagged $count';
  }

  @override
  String absentCount(int count) {
    return 'Absent $count';
  }

  @override
  String get filterAll => 'All';

  @override
  String get sessionKindTheory => 'Theory';

  @override
  String get sessionKindLab => 'Lab';

  @override
  String get sessionStatusOpen => 'Session is open';

  @override
  String get sessionStatusClosed => 'Session closed';

  @override
  String get sessionStatusScheduled => 'Not opened yet';

  @override
  String get sessionStatusCancelled => 'Cancelled';

  @override
  String get openSessionButton => 'Open session';

  @override
  String get openSessionHint =>
      'Open the session when the lecture starts so scanning begins and students see the code.';

  @override
  String get closeSessionButton => 'Close session';

  @override
  String get closeSessionNote =>
      'Closing the session stops scanning immediately.';

  @override
  String get closeSessionConfirmTitle => 'Close the session?';

  @override
  String get closeSessionConfirmBody =>
      'Students who did not scan will be marked absent and scanning stops immediately.';

  @override
  String get confirmButton => 'Confirm';

  @override
  String get cancelButton => 'Cancel';

  @override
  String absentMarkedNote(int count) {
    return '$count students were marked absent.';
  }

  @override
  String get timetableTitle => 'Weekly timetable';

  @override
  String get timetableEmpty => 'No lectures in this period';

  @override
  String timetableOffline(String time) {
    return 'Offline; showing saved data from $time';
  }

  @override
  String get changeCancelled => 'Cancelled';

  @override
  String get changeMoved => 'Moved';

  @override
  String get changeExtra => 'Extra';

  @override
  String get weekdaySunday => 'Sunday';

  @override
  String get weekdayMonday => 'Monday';

  @override
  String get weekdayTuesday => 'Tuesday';

  @override
  String get weekdayWednesday => 'Wednesday';

  @override
  String get weekdayThursday => 'Thursday';

  @override
  String get weekdayFriday => 'Friday';

  @override
  String get weekdaySaturday => 'Saturday';

  @override
  String get courseMaterialsTitle => 'Course materials';

  @override
  String get noOfferings => 'No registered courses';

  @override
  String get courseMaterialsEmpty => 'No materials published yet';

  @override
  String get materialsDownload => 'Download';

  @override
  String get materialsOpenLink => 'Open';

  @override
  String get materialsLinkOpenFailed => 'Could not open the link; try again';

  @override
  String materialsWeek(int week) {
    return 'Week $week';
  }

  @override
  String get gradesTitle => 'Your grades';

  @override
  String get gradesEmpty => 'No grades published yet';

  @override
  String get notGradedYet => 'Not graded';

  @override
  String weightedOfTotal(String total, String sum) {
    return '$total of $sum';
  }

  @override
  String scoreOfMax(String score, String max) {
    return '$score / $max';
  }

  @override
  String weightShort(String weight) {
    return 'Weight $weight%';
  }

  @override
  String get timetableCard => 'Timetable';

  @override
  String get timetableCardHint => 'Your lectures and dated changes';

  @override
  String get materialsCardHint => 'Lecture files and links';

  @override
  String get gradesCardHint => 'Published results and weighted total';

  @override
  String get gradeEntryTitle => 'Enter grades';

  @override
  String get gradeEntryHint =>
      'Enter assessment scores as a draft; publishing needs college approval';

  @override
  String get chooseOfferingLabel => 'Course';

  @override
  String get chooseAssessmentLabel => 'Assessment';

  @override
  String get noAssessmentsYet => 'No assessments yet — create one first';

  @override
  String get newAssessmentButton => 'New assessment';

  @override
  String get assessmentNameLabel => 'Assessment name';

  @override
  String get assessmentKindLabel => 'Type';

  @override
  String get maxScoreLabel => 'Maximum score';

  @override
  String get weightPercentLabel => 'Weight %';

  @override
  String get createAssessmentButton => 'Create assessment';

  @override
  String get assessmentCreated => 'Assessment created';

  @override
  String gradedOfTotal(int graded, int total) {
    return '$graded of $total entered';
  }

  @override
  String get saveDraftButton => 'Save as draft';

  @override
  String get draftSaved => 'Draft saved';

  @override
  String get publishGradesButton => 'Publish grades';

  @override
  String get publishNeedsAdmin => 'Publishing requires college admin approval';

  @override
  String publishedSuccess(int count) {
    return 'Grades published; $count students notified';
  }

  @override
  String scoreRangeError(String max) {
    return 'Score must be between 0 and $max';
  }

  @override
  String get assessmentLocked =>
      'This assessment is published and cannot be edited';

  @override
  String get assessmentPublished => 'Published';

  @override
  String get kindQuiz => 'Quiz';

  @override
  String get kindLab => 'Lab';

  @override
  String get kindMidterm => 'Midterm';

  @override
  String get kindFinal => 'Final';

  @override
  String get kindOther => 'Other';

  @override
  String get assessmentWeightHint =>
      'Total assessment weight must not exceed 100%';

  @override
  String get loginTotpLabel => 'Two-step verification code';

  @override
  String get loginTotpHint =>
      'Enter the code from your authenticator app (required for staff accounts)';

  @override
  String get totpRequiredError =>
      'This account is protected by two-step verification; enter the code and try again';

  @override
  String get totpInvalidError =>
      'The verification code is wrong or has expired';

  @override
  String get announcementsCard => 'Announcements';

  @override
  String get announcementsCardHint => 'College, department and course news';

  @override
  String get announcementsTitle => 'Announcements';

  @override
  String get announcementsEmpty => 'No announcements published yet';

  @override
  String get announcementPinned => 'Pinned';

  @override
  String get announcementPriorityHigh => 'Important';

  @override
  String get announcementMarkedRead => 'Marked as read';

  @override
  String get announcementUnknownScope => 'Announcement';

  @override
  String get inboxCard => 'Notifications';

  @override
  String get inboxCardHint => 'Inbox and device alerts';

  @override
  String get inboxTitle => 'Notifications';

  @override
  String get inboxEmpty => 'No notifications yet';

  @override
  String get markAllRead => 'Mark all as read';

  @override
  String unreadBadge(int count) {
    return '$count new';
  }

  @override
  String get notificationsPermissionDenied =>
      'Notification permission was not granted; you can still follow them in the app';

  @override
  String get notificationsEnabledMessage =>
      'Lecture notifications are enabled on this device';

  @override
  String get reminderLectureTitle => 'Lecture in 15 minutes';

  @override
  String reminderLectureBody(String course, String room, String time) {
    return '$course — $room at $time';
  }

  @override
  String get reminderDigestTitle => 'Tomorrow\'s lectures';

  @override
  String reminderDigestBody(int count, String time) {
    return '$count lectures starting at $time';
  }

  @override
  String get reminderDigestEmpty => 'No lectures tomorrow';

  @override
  String get reminderChannelName => 'Lecture reminders';

  @override
  String get reminderChannelDescription =>
      'Reminder before a lecture and a digest of tomorrow\'s lectures';

  @override
  String get excusesCard => 'Excuses';

  @override
  String get excusesCardHint =>
      'Submit an absence excuse and follow its decision';

  @override
  String get excusesTitle => 'My excuses';

  @override
  String get excusesEmpty => 'No excuses submitted';

  @override
  String get excuseNewTitle => 'New absence excuse';

  @override
  String get excuseSessionLabel => 'Lecture';

  @override
  String get excuseSelectSession => 'Select the missed lecture';

  @override
  String get excuseNoSessions =>
      'No eligible lectures (no absence within 14 days)';

  @override
  String get excuseReasonLabel => 'Reason for absence';

  @override
  String get excuseReasonHint =>
      'Explain briefly and attach the report image if available';

  @override
  String get excuseAttach => 'Attach image or PDF';

  @override
  String get excuseAttachCamera => 'Take a photo';

  @override
  String get excuseAttachGallery => 'From gallery';

  @override
  String get excuseAttachmentChosen => 'Attachment selected';

  @override
  String get excuseSubmit => 'Submit excuse';

  @override
  String get excuseSubmitted => 'Excuse sent for review';

  @override
  String get excuseStatusPending => 'Under review';

  @override
  String get excuseStatusApproved => 'Approved';

  @override
  String get excuseStatusRejected => 'Rejected';

  @override
  String get excuseReviewNote => 'Reviewer note';

  @override
  String get excuseWithdraw => 'Withdraw excuse';

  @override
  String get excuseWithdrawn => 'Excuse withdrawn';

  @override
  String get excuseWindowClosed =>
      'The excuse window for this lecture has closed (14 days)';

  @override
  String get excuseReviewTitle => 'Review excuses';

  @override
  String get excuseReviewEmpty => 'No excuses awaiting review';

  @override
  String get excuseApprove => 'Approve';

  @override
  String get excuseReject => 'Reject';

  @override
  String get excuseReviewNoteHint => 'A note shown to the student (optional)';

  @override
  String get excuseReviewed => 'Decision saved';

  @override
  String excusePendingCount(int count) {
    return 'Awaiting review: $count';
  }

  @override
  String get requestsCard => 'Requests';

  @override
  String get requestsCardHint => 'Contact your department about your studies';

  @override
  String get requestsTitle => 'My requests';

  @override
  String get requestsEmpty => 'No requests yet';

  @override
  String get requestNewTitle => 'New request';

  @override
  String get requestCategoryLabel => 'Category';

  @override
  String get requestCategoryAcademic => 'Academic matter';

  @override
  String get requestCategorySchedule => 'Timetable and rooms';

  @override
  String get requestCategoryGrades => 'Grade or assessment';

  @override
  String get requestCategoryDocuments => 'Document or letter';

  @override
  String get requestCategoryOther => 'Other';

  @override
  String get requestSubjectLabel => 'Subject';

  @override
  String get requestBodyLabel => 'Request details';

  @override
  String get requestSend => 'Send request';

  @override
  String get requestCreated => 'Your request was sent to your department';

  @override
  String get requestDetailTitle => 'Request details';

  @override
  String get requestReplyHint => 'Write your message…';

  @override
  String get requestSendReply => 'Send';

  @override
  String get requestClosedNotice => 'This request is closed; no more messages';

  @override
  String get requestStatusOpen => 'Open';

  @override
  String get requestStatusInProgress => 'In progress';

  @override
  String get requestStatusResolved => 'Resolved';

  @override
  String get requestStatusClosed => 'Closed';

  @override
  String get conversationEmpty => 'No messages yet';

  @override
  String get identityCard => 'Digital ID';

  @override
  String get identityCardHint =>
      'A signed QR card that proves your identity in exams';

  @override
  String get identityTitle => 'Your digital card';

  @override
  String get identityCardNote =>
      'Show the card to your instructor or the hall gate. It renews automatically and old screenshots stop working.';

  @override
  String identityValidFor(int seconds) {
    return 'Valid for $seconds seconds';
  }

  @override
  String get identityRefreshButton => 'Refresh card';

  @override
  String get identityVerifyTitle => 'Verify a student card';

  @override
  String get identityVerifyHint =>
      'Point the camera at the student\'s digital card';

  @override
  String get identityVerifyButton => 'Verify';

  @override
  String get identityValidTitle => 'Valid card';

  @override
  String get identityInvalidTitle => 'Invalid card';

  @override
  String get identityStudentLabel => 'Student';

  @override
  String get identityStudyTypeMorning => 'Morning';

  @override
  String get identityStudyTypeEvening => 'Evening';

  @override
  String get identityCardForStaffOnly =>
      'Card verification is available to instructors and administration';

  @override
  String get identityExpiredError =>
      'The card has expired; ask the student to refresh it';

  @override
  String get settingsCard => 'Settings';

  @override
  String get settingsCardHint =>
      'Appearance, language and two-step verification';

  @override
  String get settingsTitle => 'Settings';

  @override
  String get settingsAppearance => 'Appearance';

  @override
  String get settingsThemeLight => 'Light';

  @override
  String get settingsThemeDark => 'Dark';

  @override
  String get settingsThemeSystem => 'System';

  @override
  String get settingsLanguage => 'Language';

  @override
  String get settingsLanguageArabic => 'العربية';

  @override
  String get settingsLanguageEnglish => 'English';

  @override
  String get settingsSaved => 'Settings saved';

  @override
  String get settingsNotifications => 'Lecture notifications';

  @override
  String get settingsNotificationsHint =>
      'A reminder 15 minutes before and tomorrow\'s digest';

  @override
  String get settingsNotificationsOn => 'Enabled on this device';

  @override
  String get settingsNotificationsOff => 'Not enabled';

  @override
  String get enableNotificationsButton => 'Enable notifications';

  @override
  String get twoFactorTitle => 'Two-step verification';

  @override
  String get twoFactorHint =>
      'Extra protection for instructor and admin accounts via an authenticator app';

  @override
  String get twoFactorEnabled => 'Enabled';

  @override
  String get twoFactorDisabled => 'Disabled';

  @override
  String get twoFactorSetup => 'Start setup';

  @override
  String get twoFactorSecretLabel =>
      'Secret (enter it manually if the code cannot be scanned)';

  @override
  String get twoFactorCodeLabel => 'App code (6 digits)';

  @override
  String get twoFactorEnable => 'Enable';

  @override
  String get twoFactorDisable => 'Disable';

  @override
  String get twoFactorPasswordLabel => 'Password to confirm disabling';

  @override
  String get twoFactorEnabledMessage => 'Two-step verification enabled';

  @override
  String get twoFactorDisabledMessage => 'Two-step verification disabled';

  @override
  String get twoFactorNotAvailable =>
      'Available for instructor and admin accounts only';

  @override
  String get twoFactorSetupHint =>
      'Add the secret to Google Authenticator or any TOTP app, then enter the shown code.';

  @override
  String dataFromCache(String time) {
    return 'Offline; showing saved data from $time';
  }

  @override
  String get offlineSavedHint =>
      'Data refreshes automatically when the connection returns';
}
