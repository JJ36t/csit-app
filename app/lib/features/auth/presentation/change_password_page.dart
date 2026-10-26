import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../l10n/app_localizations.dart';
import 'session.dart';

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
