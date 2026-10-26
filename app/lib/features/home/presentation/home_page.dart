import 'package:flutter/material.dart';

import '../../../core/app_services.dart';
import '../../../l10n/app_localizations.dart';
import '../../announcements/presentation/announcements_page.dart';
import '../../attendance/presentation/scan_page.dart';
import '../../attendance/presentation/sessions_page.dart';
import '../../auth/presentation/change_password_page.dart';
import '../../auth/presentation/session.dart';
import '../../grades/presentation/grades_page.dart';
import '../../materials/presentation/materials_page.dart';
import '../../notifications/presentation/notifications_page.dart';
import '../../profile_settings/presentation/profile_page.dart';
import '../../timetable/presentation/timetable_page.dart';

/// الرئيسية: ترحيب بالمستخدم ومداخل «يوم الطالب»
/// (الحضور، الجدول، المواد، الدرجات، الإعلانات، الإشعارات، الملف الشخصي).
class HomePage extends StatefulWidget {
  const HomePage({super.key, required this.session, required this.services});

  final SessionController session;
  final AppServices services;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _unreadNotifications = 0;

  @override
  void initState() {
    super.initState();
    _loadUnreadNotifications();
  }

  /// شارة صندوق الوارد تحسينية: فشل التحميل يُبقيها مخفية ولا يعطّل الرئيسية.
  Future<void> _loadUnreadNotifications() async {
    try {
      final inbox = await widget.services.notifications.inbox();
      if (!mounted) {
        return;
      }
      setState(() => _unreadNotifications = inbox.unreadCount);
    } catch (_) {
      // تجاهل: الشارة اختيارية.
    }
  }

  Future<void> _openNotifications() async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => NotificationsPage(
          api: widget.services.notifications,
          session: widget.session,
        ),
      ),
    );
    if (!mounted) {
      return;
    }
    await _loadUnreadNotifications();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final session = widget.session;
    final services = widget.services;
    final profile = session.profile;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.homeTitle),
        actions: [
          IconButton(
            key: const Key('logoutButton'),
            tooltip: l10n.logoutButton,
            onPressed: session.isBusy ? null : session.logout,
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
                const SizedBox(height: 16),
                if (profile.isStudent)
                  Card(
                    child: ListTile(
                      key: const Key('scanAttendanceCard'),
                      leading: const Icon(Icons.qr_code_scanner),
                      title: Text(l10n.scanAttendanceCard),
                      subtitle: Text(l10n.scanAttendanceCardHint),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) => ScanPage(
                            api: services.attendance,
                            session: session,
                          ),
                        ),
                      ),
                    ),
                  ),
                if (profile.isInstructor)
                  Card(
                    child: ListTile(
                      key: const Key('todaySessionsCard'),
                      leading: const Icon(Icons.event_available_outlined),
                      title: Text(l10n.todaySessionsCard),
                      subtitle: Text(l10n.todaySessionsCardHint),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) => SessionsPage(
                            api: services.attendance,
                            session: session,
                          ),
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
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => TimetablePage(
                          api: services.timetable,
                          session: session,
                        ),
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
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => MaterialsPage(
                          api: services.materials,
                          session: session,
                        ),
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
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) => GradesPage(
                            api: services.grades,
                            session: session,
                          ),
                        ),
                      ),
                    ),
                  ),
                Card(
                  child: ListTile(
                    key: const Key('announcementsCard'),
                    leading: const Icon(Icons.campaign_outlined),
                    title: Text(l10n.announcementsTitle),
                    subtitle: Text(l10n.announcementsCardHint),
                    trailing: const Icon(Icons.chevron_left),
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => AnnouncementsPage(
                          api: services.announcements,
                          session: session,
                        ),
                      ),
                    ),
                  ),
                ),
                Card(
                  child: ListTile(
                    key: const Key('notificationsCard'),
                    leading: const Icon(Icons.notifications_none),
                    title: Text(l10n.notificationsTitle),
                    subtitle: Text(l10n.notificationsCardHint),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (_unreadNotifications > 0)
                          Badge(
                            key: const Key('notificationsBadge'),
                            label: Text('$_unreadNotifications'),
                          ),
                        const Icon(Icons.chevron_left),
                      ],
                    ),
                    onTap: _openNotifications,
                  ),
                ),
                Card(
                  child: ListTile(
                    key: const Key('profileCard'),
                    leading: const Icon(Icons.person_outline),
                    title: Text(l10n.profileTitle),
                    subtitle: Text(l10n.profileCardHint),
                    trailing: const Icon(Icons.chevron_left),
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => ProfilePage(session: session),
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
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) => ChangePasswordPage(session: session),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
    );
  }
}