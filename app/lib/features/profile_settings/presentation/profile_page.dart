import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/presentation/change_password_page.dart';
import '../../auth/presentation/session.dart';

/// الملف الشخصي: بيانات الحساب من `SessionProfile`، مع تغيير كلمة المرور والخروج.
class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key, required this.session});

  final SessionController session;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final profile = session.profile;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.profileTitle)),
      body: SafeArea(
        child: profile == null
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Card(
                    margin: EdgeInsets.zero,
                    child: Column(
                      children: [
                        _ProfileRow(
                          rowKey: const Key('profileName'),
                          icon: Icons.person_outline,
                          label: l10n.fullNameLabel,
                          value: profile.fullNameAr,
                        ),
                        _ProfileRow(
                          rowKey: const Key('profileUniversityId'),
                          icon: Icons.badge_outlined,
                          label: l10n.universityIdLabel,
                          value: profile.universityId,
                        ),
                        _ProfileRow(
                          rowKey: const Key('profileRole'),
                          icon: Icons.workspace_premium_outlined,
                          label: l10n.roleLabel,
                          value: _roleLabel(l10n, profile),
                        ),
                        if (profile.departmentName != null)
                          _ProfileRow(
                            rowKey: const Key('profileDepartment'),
                            icon: Icons.account_tree_outlined,
                            label: l10n.departmentLabel,
                            value: profile.departmentName!,
                          ),
                        if (profile.stage != null)
                          _ProfileRow(
                            rowKey: const Key('profileStage'),
                            icon: Icons.layers_outlined,
                            label: l10n.stageLabel,
                            value: '${profile.stage}',
                          ),
                        if (profile.groupName != null)
                          _ProfileRow(
                            rowKey: const Key('profileGroup'),
                            icon: Icons.groups_outlined,
                            label: l10n.groupLabel,
                            value: profile.groupName!,
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  Card(
                    margin: EdgeInsets.zero,
                    child: Column(
                      children: [
                        ListTile(
                          key: const Key('profileChangePassword'),
                          leading: const Icon(Icons.key_outlined),
                          title: Text(l10n.changePasswordTitle),
                          trailing: const Icon(Icons.chevron_left),
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute<void>(
                              builder: (_) =>
                                  ChangePasswordPage(session: session),
                            ),
                          ),
                        ),
                        ListTile(
                          key: const Key('profileLogout'),
                          leading: const Icon(Icons.logout),
                          title: Text(l10n.logoutButton),
                          onTap: session.isBusy ? null : session.logout,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
      ),
    );
  }

  /// اسم الدور بالعربية من الترجمة، وليس من نص الخادم.
  String _roleLabel(AppLocalizations l10n, UserProfile profile) {
    switch (profile.role) {
      case 'instructor':
        return l10n.roleInstructor;
      case 'department_head':
        return l10n.roleDepartmentHead;
      case 'college_admin':
        return l10n.roleCollegeAdmin;
      default:
        return l10n.roleStudent;
    }
  }
}

class _ProfileRow extends StatelessWidget {
  const _ProfileRow({
    required this.rowKey,
    required this.icon,
    required this.label,
    required this.value,
  });

  final Key rowKey;
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      key: rowKey,
      leading: Icon(icon),
      title: Text(label),
      subtitle: Text(value),
    );
  }
}
