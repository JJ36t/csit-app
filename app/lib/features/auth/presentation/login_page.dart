import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../l10n/app_localizations.dart';
import 'session.dart';

/// شاشة الدخول: الرقم الجامعي + كلمة المرور، وربط الجهاز يجري على الخادم.
class LoginPage extends StatefulWidget {
  const LoginPage({super.key, required this.session});

  final SessionController session;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _idController = TextEditingController();
  final _passwordController = TextEditingController();
  String? _error;
  bool _submitting = false;

  @override
  void dispose() {
    _idController.dispose();
    _passwordController.dispose();
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
      await widget.session.login(
        universityId: _idController.text,
        password: _passwordController.text,
      );
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _error = error.messageAr ?? _localizedError(l10n, error.code);
      });
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() => _error = l10n.unexpectedError);
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  String _localizedError(AppLocalizations l10n, String code) {
    switch (code) {
      case 'network_unreachable':
        return l10n.networkUnreachable;
      case 'session_expired':
      case 'not_authenticated':
        return l10n.sessionExpired;
      default:
        return l10n.unexpectedError;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final busy = _submitting || widget.session.isBusy;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Icon(
                      Icons.school_outlined,
                      size: 64,
                      color: theme.colorScheme.primary,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      l10n.appTitle,
                      textAlign: TextAlign.center,
                      style: theme.textTheme.headlineSmall
                          ?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      l10n.collegeName,
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodySmall,
                    ),
                    const SizedBox(height: 28),
                    Text(
                      l10n.loginTitle,
                      style: theme.textTheme.titleLarge,
                    ),
                    Text(l10n.loginSubtitle, style: theme.textTheme.bodySmall),
                    const SizedBox(height: 16),
                    TextFormField(
                      key: const Key('universityIdField'),
                      controller: _idController,
                      textInputAction: TextInputAction.next,
                      enabled: !busy,
                      decoration: InputDecoration(
                        labelText: l10n.universityIdLabel,
                        prefixIcon: const Icon(Icons.badge_outlined),
                        border: const OutlineInputBorder(),
                      ),
                      validator: (value) {
                        final text = (value ?? '').trim();
                        if (text.isEmpty) {
                          return l10n.fieldRequired;
                        }
                        if (text.length < 3) {
                          return l10n.universityIdInvalid;
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      key: const Key('passwordField'),
                      controller: _passwordController,
                      obscureText: true,
                      enabled: !busy,
                      onFieldSubmitted: (_) => _submit(),
                      decoration: InputDecoration(
                        labelText: l10n.passwordLabel,
                        prefixIcon: const Icon(Icons.lock_outline),
                        border: const OutlineInputBorder(),
                      ),
                      validator: (value) =>
                          (value == null || value.isEmpty) ? l10n.fieldRequired : null,
                    ),
                    const SizedBox(height: 16),
                    if (_error != null) ...[
                      Container(
                        key: const Key('loginError'),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.errorContainer,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          _error!,
                          style: TextStyle(color: theme.colorScheme.onErrorContainer),
                        ),
                      ),
                      const SizedBox(height: 12),
                    ],
                    FilledButton(
                      key: const Key('loginButton'),
                      onPressed: busy ? null : _submit,
                      style: FilledButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      child: busy
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(l10n.loginButton),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
