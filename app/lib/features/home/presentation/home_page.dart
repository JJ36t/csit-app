import 'package:flutter/material.dart';

import '../../../core/app_services.dart';
import '../../../core/network/api_client.dart';
import '../../../core/notifications/local_notifications.dart';
import '../../../core/notifications/push_service.dart';
import '../../../core/notifications/reminder_plan.dart';
import '../../../core/settings/app_settings.dart';
import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../../announcements/data/announcements_api.dart';
import '../../announcements/presentation/announcements_page.dart';
import '../../attendance/presentation/scan_page.dart';
import '../../attendance/presentation/sessions_page.dart';
import '../../auth/presentation/session.dart';
import '../../excuses/presentation/excuses_page.dart';
import '../../grades/presentation/grade_entry_page.dart';
import '../../grades/presentation/grades_page.dart';
import '../../identity/presentation/identity_card_page.dart';
import '../../identity/presentation/identity_verify_page.dart';
import '../../materials/presentation/materials_page.dart';
import '../../notifications/presentation/inbox_page.dart';
import '../../requests/presentation/requests_page.dart';
import '../../settings/presentation/settings_page.dart';
import '../../timetable/data/timetable_api.dart';
import '../../timetable/presentation/timetable_page.dart';

/// الرئيسية: ترحيب بالمستخدم وبياناته ومداخل «يوم الطالب»
/// (الحضور، الجدول، الإعلانات، المواد، الدرجات، الأعذار، الطلبات، الهوية).
class HomePage extends StatefulWidget {
  const HomePage({
    super.key,
    required this.session,
    required this.services,
    required this.settings,
    this.reminders,
    this.push,
  });

  final SessionController session;
  final AppServices services;
  final AppSettings settings;
  final LocalNotificationService? reminders;
  final PushService? push;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _unread = 0;
  List<SessionItem> _today = const [];
  AnnouncementItem? _latestAnnouncement;

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    await _loadUnread();
    final sessions = await _loadSummary();
    await _prepareNotifications(sessions);
  }

  /// محاضرات اليوم وآخر إعلان — نفس بيانات الشاشتين، مع ذاكرة عند انقطاع الشبكة.
  Future<List<SessionItem>> _loadSummary() async {
    var sessions = const <SessionItem>[];
    try {
      final timetable = await widget.services.timetable.load();
      sessions = timetable.sessions;
      final now = DateTime.now().toUtc();
      final todays = sessions
          .where(
            (session) =>
                session.status != 'cancelled' && isSameBaghdadDay(session.startsAt, now),
          )
          .toList()
        ..sort((a, b) => a.startsAt.compareTo(b.startsAt));
      if (mounted) {
        setState(() => _today = todays);
      }
    } catch (_) {
      // الجدول ميزة مساعدة هنا؛ تُعرض قائمة فارغة بدل تعطيل الرئيسية
    }
    try {
      final announcements = await widget.services.announcements.load();
      if (mounted && announcements.items.isNotEmpty) {
        setState(() => _latestAnnouncement = announcements.items.first);
      }
    } catch (_) {
      // لا إعلان محفوظ بعد
    }
    return sessions;
  }

  Future<void> _loadUnread() async {
    try {
      final data = await widget.services.notifications.load();
      if (!mounted) {
        return;
      }
      setState(() => _unread = data.unreadCount);
    } catch (_) {
      // لا نعطّل الرئيسية لفشل عدّاد الإشعارات
    }
  }

  /// يهيّئ قناة الإشعارات المحلية ثم يجدول تذكيرات المحاضرات من الجدول.
  /// نقرأ l10n بعد كل `await` مع فحص mounted (فخ معروف في هذا المشروع).
  Future<void> _prepareNotifications(List<SessionItem> sessions) async {
    if (widget.reminders == null) {
      return;
    }
    try {
      final l10n = AppLocalizations.of(context)!;
      await widget.reminders!.initialize(
        channelName: l10n.reminderChannelName,
        channelDescription: l10n.reminderChannelDescription,
      );
      await widget.push?.initialize();
      if (!mounted) {
        return;
      }
      final plan = buildReminderPlan(
        sessions: sessions,
        now: DateTime.now(),
        lectureTitle: (_) => l10n.reminderLectureTitle,
        lectureBody: (session) => l10n.reminderLectureBody(
          session.courseNameAr,
          session.room ?? '',
          formatHm(session.startsAt),
        ),
        digestTitle: l10n.reminderDigestTitle,
        digestBody: (count, time) => l10n.reminderDigestBody(count, time),
      );
      await widget.reminders!.schedule(plan);
    } catch (_) {
      // الإشعارات ميزة مساعدة: فشل التهيئة لا يمنع استخدام التطبيق
    }
  }

  Future<void> _push(Widget page) async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(builder: (_) => page),
    );
    await _loadUnread();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final profile = widget.session.profile;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.homeTitle),
        actions: [
          IconButton(
            key: const Key('inboxButton'),
            tooltip: l10n.inboxTitle,
            onPressed: () => _push(
              InboxPage(api: widget.services.notifications, session: widget.session),
            ),
            icon: Badge.count(
              count: _unread,
              isLabelVisible: _unread > 0,
              child: const Icon(Icons.notifications_outlined),
            ),
          ),
          IconButton(
            key: const Key('settingsButton'),
            tooltip: l10n.settingsTitle,
            onPressed: () => _push(
              SettingsPage(
                settings: widget.settings,
                twoFactor: widget.services.twoFactor,
                session: widget.session,
                reminders: widget.reminders,
                timetable: widget.services.timetable,
              ),
            ),
            icon: const Icon(Icons.settings_outlined),
          ),
          IconButton(
            key: const Key('logoutButton'),
            tooltip: l10n.logoutButton,
            onPressed: widget.session.isBusy ? null : widget.session.logout,
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: profile == null
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(
                  '${l10n.welcome} ${profile.fullNameAr}',
                  style: theme.textTheme.titleLarge,
                ),
                const SizedBox(height: 4),
                Text(
                  profile.universityId,
                  style: theme.textTheme.bodyMedium,
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        l10n.homeTodayLectures,
                        style: theme.textTheme.titleMedium,
                      ),
                    ),
                    TextButton(
                      key: const Key('homeTimetableLink'),
                      onPressed: () => _push(
                        TimetablePage(
                          api: widget.services.timetable,
                          session: widget.session,
                        ),
                      ),
                      child: Text(l10n.homeViewAll),
                    ),
                  ],
                ),
                if (_today.isEmpty)
                  Card(
                    child: ListTile(
                      leading: const Icon(Icons.event_busy_outlined),
                      title: Text(l10n.homeNoLectures),
                    ),
                  )
                else
                  for (final session in _today.take(3))
                    Card(
                      child: ListTile(
                        leading: SizedBox(
                          width: 52,
                          child: Text(
                            formatHm(session.startsAt),
                            style: theme.textTheme.titleSmall,
                          ),
                        ),
                        title: Text(session.courseNameAr),
                        subtitle: Text(
                          [
                            if (session.room != null) session.room!,
                            session.kind == 'lab'
                                ? l10n.sessionKindLab
                                : l10n.sessionKindTheory,
                          ].join(' · '),
                        ),
                      ),
                    ),
                if (_latestAnnouncement != null)
                  Card(
                    child: ListTile(
                      key: const Key('homeLatestAnnouncement'),
                      leading: const Icon(Icons.campaign_outlined),
                      title: Text(l10n.homeLatestAnnouncement),
                      subtitle: Text(
                        _latestAnnouncement!.title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _push(
                        AnnouncementsPage(
                          api: widget.services.announcements,
                          session: widget.session,
                        ),
                      ),
                    ),
                  ),
                const SizedBox(height: 16),
                if (profile.isStudent)
                  Card(
                    child: ListTile(
                      key: const Key('scanAttendanceCard'),
                      leading: const Icon(Icons.qr_code_scanner),
                      title: Text(l10n.scanAttendanceCard),
                      subtitle: Text(l10n.scanAttendanceCardHint),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _push(
                        ScanPage(
                          api: widget.services.attendance,
                          session: widget.session,
                        ),
                      ),
                    ),
                  ),
                if (profile.isStudent)
                  Card(
                    child: ListTile(
                      key: const Key('identityCard'),
                      leading: const Icon(Icons.badge_outlined),
                      title: Text(l10n.identityCard),
                      subtitle: Text(l10n.identityCardHint),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _push(
                        IdentityCardPage(
                          api: widget.services.identity,
                          session: widget.session,
                        ),
                      ),
                    ),
                  ),
                if (!profile.isStudent)
                  Card(
                    child: ListTile(
                      key: const Key('todaySessionsCard'),
                      leading: const Icon(Icons.event_available_outlined),
                      title: Text(l10n.todaySessionsCard),
                      subtitle: Text(l10n.todaySessionsCardHint),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _push(
                        SessionsPage(
                          api: widget.services.attendance,
                          session: widget.session,
                        ),
                      ),
                    ),
                  ),
                Card(
                  child: ListTile(
                    key: const Key('timetableCard'),
                    leading: const Icon(Icons.calendar_month_outlined),
                    title: Text(l10n.timetableCard),
                    subtitle: Text(l10n.timetableCardHint),
                    trailing: const Icon(Icons.chevron_left),
                    onTap: () => _push(
                      TimetablePage(
                        api: widget.services.timetable,
                        session: widget.session,
                      ),
                    ),
                  ),
                ),
                Card(
                  child: ListTile(
                    key: const Key('announcementsCard'),
                    leading: const Icon(Icons.campaign_outlined),
                    title: Text(l10n.announcementsCard),
                    subtitle: Text(l10n.announcementsCardHint),
                    trailing: const Icon(Icons.chevron_left),
                    onTap: () => _push(
                      AnnouncementsPage(
                        api: widget.services.announcements,
                        session: widget.session,
                      ),
                    ),
                  ),
                ),
                Card(
                  child: ListTile(
                    key: const Key('materialsCard'),
                    leading: const Icon(Icons.folder_open_outlined),
                    title: Text(l10n.courseMaterialsTitle),
                    subtitle: Text(l10n.materialsCardHint),
                    trailing: const Icon(Icons.chevron_left),
                    onTap: () => _push(
                      MaterialsPage(
                        api: widget.services.materials,
                        session: widget.session,
                      ),
                    ),
                  ),
                ),
                if (profile.isStudent)
                  Card(
                    child: ListTile(
                      key: const Key('gradesCard'),
                      leading: const Icon(Icons.insights_outlined),
                      title: Text(l10n.gradesTitle),
                      subtitle: Text(l10n.gradesCardHint),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _push(
                        GradesPage(
                          api: widget.services.grades,
                          session: widget.session,
                        ),
                      ),
                    ),
                  ),
                if (profile.isStudent)
                  Card(
                    child: ListTile(
                      key: const Key('excusesCard'),
                      leading: const Icon(Icons.assignment_late_outlined),
                      title: Text(l10n.excusesCard),
                      subtitle: Text(l10n.excusesCardHint),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _push(
                        ExcusesPage(
                          api: widget.services.excuses,
                          session: widget.session,
                        ),
                      ),
                    ),
                  ),
                if (!profile.isStudent)
                  Card(
                    child: ListTile(
                      key: const Key('excuseReviewCard'),
                      leading: const Icon(Icons.fact_check_outlined),
                      title: Text(l10n.excuseReviewTitle),
                      subtitle: Text(l10n.excuseReviewEmpty),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _push(
                        ExcusesPage(
                          api: widget.services.excuses,
                          session: widget.session,
                          reviewMode: true,
                        ),
                      ),
                    ),
                  ),
                if (!profile.isStudent)
                  Card(
                    child: ListTile(
                      key: const Key('identityVerifyCard'),
                      leading: const Icon(Icons.verified_user_outlined),
                      title: Text(l10n.identityVerifyTitle),
                      subtitle: Text(l10n.identityVerifyHint),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _push(
                        IdentityVerifyPage(
                          api: widget.services.identity,
                          session: widget.session,
                        ),
                      ),
                    ),
                  ),
                if (!profile.isStudent)
                  Card(
                    child: ListTile(
                      key: const Key('gradeEntryCard'),
                      leading: const Icon(Icons.edit_note_outlined),
                      title: Text(l10n.gradeEntryTitle),
                      subtitle: Text(l10n.gradeEntryHint),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _push(
                        GradeEntryPage(
                          api: widget.services.gradeEntry,
                          offeringsApi: widget.services.materials,
                          session: widget.session,
                        ),
                      ),
                    ),
                  ),
                Card(
                  child: ListTile(
                    key: const Key('requestsCard'),
                    leading: const Icon(Icons.forum_outlined),
                    title: Text(
                      profile.isStudent ? l10n.requestsTitle : l10n.requestsCard,
                    ),
                    subtitle: Text(l10n.requestsCardHint),
                    trailing: const Icon(Icons.chevron_left),
                    onTap: () => _push(
                      RequestsPage(
                        api: widget.services.requests,
                        session: widget.session,
                      ),
                    ),
                  ),
                ),
                if (profile.departmentName != null)
                  Card(
                    child: ListTile(
                      leading: const Icon(Icons.account_tree_outlined),
                      title: Text(l10n.departmentLabel),
                      subtitle: Text(profile.departmentName!),
                    ),
                  ),
                if (profile.stage != null)
                  Card(
                    child: ListTile(
                      leading: const Icon(Icons.layers_outlined),
                      title: Text(l10n.stageLabel),
                      subtitle: Text('${profile.stage}'),
                    ),
                  ),
                if (profile.groupName != null)
                  Card(
                    child: ListTile(
                      leading: const Icon(Icons.groups_outlined),
                      title: Text(l10n.groupLabel),
                      subtitle: Text(profile.groupName!),
                    ),
                  ),
                if (profile.mustChangePassword)
                  Card(
                    color: theme.colorScheme.tertiaryContainer,
                    child: ListTile(
                      leading: const Icon(Icons.key_outlined),
                      title: Text(l10n.mustChangePasswordNotice),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _push(ChangePasswordPage(session: widget.session)),
                    ),
                  ),
              ],
            ),
    );
  }
}

/// شاشة تغيير كلمة المرور — إجبارية بعد أول دخول بحسب الخطة.
class ChangePasswordPage extends StatefulWidget {
  const ChangePasswordPage({super.key, required this.session});

  final SessionController session;

  @override
  State<ChangePasswordPage> createState() => _ChangePasswordPageState();
}

class _ChangePasswordPageState extends State<ChangePasswordPage> {
  final _formKey = GlobalKey<FormState>();
  final _currentController = TextEditingController();
  final _newController = TextEditingController();
  String? _error;
  bool _submitting = false;

  @override
  void dispose() {
    _currentController.dispose();
    _newController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context)!;
    setState(() => _error = null);
    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }
    setState(() => _submitting = true);
    try {
      await widget.session.changePassword(
        currentPassword: _currentController.text,
        newPassword: _newController.text,
      );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.passwordChanged)),
      );
      Navigator.of(context).pop();
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _error = error.messageAr ?? l10n.unexpectedError);
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.changePasswordTitle)),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              key: const Key('currentPasswordField'),
              controller: _currentController,
              obscureText: true,
              decoration: InputDecoration(
                labelText: l10n.currentPasswordLabel,
                border: const OutlineInputBorder(),
              ),
              validator: (value) =>
                  (value == null || value.isEmpty) ? l10n.fieldRequired : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              key: const Key('newPasswordField'),
              controller: _newController,
              obscureText: true,
              decoration: InputDecoration(
                labelText: l10n.newPasswordLabel,
                border: const OutlineInputBorder(),
              ),
              validator: (value) => (value == null || value.length < 8)
                  ? l10n.passwordTooShort
                  : null,
            ),
            const SizedBox(height: 16),
            if (_error != null) ...[
              Text(
                _error!,
                key: const Key('changePasswordError'),
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
              const SizedBox(height: 12),
            ],
            FilledButton(
              key: const Key('changePasswordButton'),
              onPressed: _submitting ? null : _submit,
              child: Text(l10n.changePasswordButton),
            ),
          ],
        ),
      ),
    );
  }
}
