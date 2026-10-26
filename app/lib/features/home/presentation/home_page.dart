import 'package:flutter/material.dart';

import '../../../core/app_services.dart';
import '../../../core/network/api_client.dart';
import '../../../l10n/app_localizations.dart';
import '../../attendance/presentation/scan_page.dart';
import '../../attendance/presentation/sessions_page.dart';
import '../../auth/presentation/session.dart';
import '../../grades/presentation/grades_page.dart';
import '../../materials/presentation/materials_page.dart';
import '../../timetable/presentation/timetable_page.dart';

/// الرئيسية: ترحيب بالمستخدم وبياناته ومداخل «يوم الطالب»
/// (الحضور، الجدول، المواد، الدرجات) وزر الخروج.
class HomePage extends StatelessWidget {
  const HomePage({super.key, required this.session, required this.services});

  final SessionController session;
  final AppServices services;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
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
