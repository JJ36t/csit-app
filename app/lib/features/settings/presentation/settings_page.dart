import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/notifications/local_notifications.dart';
import '../../../core/notifications/reminder_plan.dart';
import '../../../core/settings/app_settings.dart';
import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../../timetable/data/timetable_api.dart';
import '../data/two_factor_api.dart';

/// الإعدادات: المظهر، اللغة، إشعارات المحاضرات، والتحقق بخطوتين.
class SettingsPage extends StatefulWidget {
  const SettingsPage({
    super.key,
    required this.settings,
    required this.twoFactor,
    required this.session,
    this.reminders,
    this.timetable,
  });

  final AppSettings settings;
  final TwoFactorApi twoFactor;
  final SessionController session;
  final LocalNotificationService? reminders;
  final TimetableApi? timetable;

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  TwoFactorStatus? _status;
  bool _loadingStatus = true;
  bool _notificationsOn = false;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _loadStatus();
  }

  Future<void> _loadStatus() async {
    try {
      final status = await widget.twoFactor.status();
      if (!mounted) {
        return;
      }
      setState(() {
        _status = status;
        _loadingStatus = false;
      });
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() => _loadingStatus = false);
    }
  }

  Future<void> _enableNotifications() async {
    final l10n = AppLocalizations.of(context)!;
    final reminders = widget.reminders;
    if (reminders == null) {
      return;
    }
    setState(() => _busy = true);
    try {
      await reminders.initialize(
        channelName: l10n.reminderChannelName,
        channelDescription: l10n.reminderChannelDescription,
      );
      final timetable = await widget.timetable?.load();
      if (timetable != null && mounted) {
        final plan = buildReminderPlan(
          sessions: timetable.sessions,
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
        await reminders.schedule(plan);
      }
      if (!mounted) {
        return;
      }
      setState(() => _notificationsOn = reminders.isInitialized);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.notificationsEnabledMessage)),
      );
    } catch (_) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.notificationsPermissionDenied)),
      );
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }

  Future<void> _setupTwoFactor() async {
    final l10n = AppLocalizations.of(context)!;
    try {
      final setup = await widget.twoFactor.setup();
      if (!mounted) {
        return;
      }
      final controller = TextEditingController();
      final enabled = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(l10n.twoFactorTitle),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.twoFactorSetupHint),
                const SizedBox(height: 12),
                SelectableText(
                  setup.secret,
                  key: const Key('twoFactorSecret'),
                  style: const TextStyle(fontFamily: 'monospace'),
                ),
                const SizedBox(height: 12),
                TextField(
                  key: const Key('twoFactorCodeField'),
                  controller: controller,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: l10n.twoFactorCodeLabel,
                    border: const OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: Text(l10n.cancelButton),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: Text(l10n.twoFactorEnable),
            ),
          ],
        ),
      );
      if (enabled != true) {
        return;
      }
      await widget.twoFactor.enable(controller.text.trim());
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.twoFactorEnabledMessage)),
      );
      await _loadStatus();
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    }
  }

  Future<void> _disableTwoFactor() async {
    final l10n = AppLocalizations.of(context)!;
    final controller = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.twoFactorDisable),
        content: TextField(
          key: const Key('twoFactorPasswordField'),
          controller: controller,
          obscureText: true,
          decoration: InputDecoration(
            labelText: l10n.twoFactorPasswordLabel,
            border: const OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.cancelButton),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.confirmButton),
          ),
        ],
      ),
    );
    if (confirmed != true) {
      return;
    }
    try {
      await widget.twoFactor.disable(controller.text);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.twoFactorDisabledMessage)),
      );
      await _loadStatus();
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final settings = widget.settings;
    final status = _status;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.settingsTitle)),
      body: ListenableBuilder(
        listenable: settings,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(l10n.settingsAppearance, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            SegmentedButton<ThemeMode>(
              key: const Key('themeSelector'),
              segments: [
                ButtonSegment(
                  value: ThemeMode.light,
                  icon: const Icon(Icons.light_mode_outlined),
                  label: Text(l10n.settingsThemeLight),
                ),
                ButtonSegment(
                  value: ThemeMode.dark,
                  icon: const Icon(Icons.dark_mode_outlined),
                  label: Text(l10n.settingsThemeDark),
                ),
                ButtonSegment(
                  value: ThemeMode.system,
                  icon: const Icon(Icons.brightness_auto_outlined),
                  label: Text(l10n.settingsThemeSystem),
                ),
              ],
              selected: {settings.themeMode},
              onSelectionChanged: (value) => settings.setThemeMode(value.first),
            ),
            const SizedBox(height: 20),
            Text(l10n.settingsLanguage, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              key: const Key('languageSelector'),
              segments: [
                ButtonSegment(value: 'ar', label: Text(l10n.settingsLanguageArabic)),
                ButtonSegment(value: 'en', label: Text(l10n.settingsLanguageEnglish)),
              ],
              selected: {settings.localeCode},
              onSelectionChanged: (value) => settings.setLocale(value.first),
            ),
            const Divider(height: 32),
            Card(
              child: ListTile(
                leading: const Icon(Icons.alarm_outlined),
                title: Text(l10n.settingsNotifications),
                subtitle: Text(
                  _notificationsOn
                      ? l10n.settingsNotificationsOn
                      : l10n.settingsNotificationsHint,
                ),
                trailing: FilledButton.tonal(
                  key: const Key('enableNotificationsButton'),
                  onPressed: _busy ? null : _enableNotifications,
                  child: Text(l10n.enableNotificationsButton),
                ),
              ),
            ),
            const Divider(height: 32),
            Text(l10n.twoFactorTitle, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text(l10n.twoFactorHint, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 8),
            if (_loadingStatus)
              const LinearProgressIndicator()
            else if (status == null || !status.available)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.lock_outline),
                  title: Text(l10n.twoFactorNotAvailable),
                ),
              )
            else
              Card(
                child: ListTile(
                  leading: Icon(
                    status.enabled ? Icons.verified_user : Icons.gpp_maybe_outlined,
                  ),
                  title: Text(
                    status.enabled ? l10n.twoFactorEnabled : l10n.twoFactorDisabled,
                  ),
                  trailing: status.enabled
                      ? OutlinedButton(
                          key: const Key('disableTwoFactorButton'),
                          onPressed: _disableTwoFactor,
                          child: Text(l10n.twoFactorDisable),
                        )
                      : FilledButton(
                          key: const Key('setupTwoFactorButton'),
                          onPressed: _setupTwoFactor,
                          child: Text(l10n.twoFactorSetup),
                        ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
