import 'dart:async';

import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../l10n/app_localizations.dart';
import '../../attendance/data/attendance_scanner.dart';
import '../../auth/presentation/session.dart';
import '../data/identity_api.dart';

/// التحقق من بطاقة طالب: يمسح التدريسي رمز QR فيتأكد الخادم من التوقيع والصلاحية.
class IdentityVerifyPage extends StatefulWidget {
  const IdentityVerifyPage({
    super.key,
    required this.api,
    required this.session,
    this.scanner,
  });

  final IdentityApi api;
  final SessionController session;
  final AttendanceScanner? scanner;

  @override
  State<IdentityVerifyPage> createState() => _IdentityVerifyPageState();
}

class _IdentityVerifyPageState extends State<IdentityVerifyPage> {
  late final AttendanceScanner _scanner =
      widget.scanner ?? MobileScannerAttendanceScanner();
  StreamSubscription<String>? _subscription;
  VerifiedStudent? _result;
  String? _error;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _subscribe();
  }

  void _subscribe() {
    _subscription?.cancel();
    _subscription = _scanner.codes.listen(_onCode);
  }

  Future<void> _onCode(String code) async {
    if (_busy || _result != null) {
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final student = await widget.api.verify(code);
      if (!mounted) {
        return;
      }
      setState(() {
        _result = student;
        _busy = false;
      });
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      if (error.statusCode == 401) {
        widget.session.expire();
        return;
      }
      setState(() {
        _error = error.messageAr ?? AppLocalizations.of(context)!.unexpectedError;
        _busy = false;
      });
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() {
        _error = AppLocalizations.of(context)!.unexpectedError;
        _busy = false;
      });
    }
  }

  void _rescan() {
    setState(() {
      _result = null;
      _error = null;
      _busy = false;
    });
    _subscribe();
  }

  @override
  void dispose() {
    _subscription?.cancel();
    _scanner.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final student = _result;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.identityVerifyTitle)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (student == null) ...[
              AspectRatio(
                aspectRatio: 1,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      _scanner.buildPreview(),
                      if (_busy)
                        ColoredBox(
                          color: Colors.black38,
                          child: const Center(child: CircularProgressIndicator()),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                l10n.identityVerifyHint,
                textAlign: TextAlign.center,
                style: theme.textTheme.titleSmall,
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(
                  _error!,
                  key: const Key('identityVerifyError'),
                  textAlign: TextAlign.center,
                  style: TextStyle(color: theme.colorScheme.error),
                ),
              ],
            ] else ...[
              Card(
                color: theme.colorScheme.primaryContainer,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.verified_user, color: theme.colorScheme.primary),
                          const SizedBox(width: 8),
                          Text(
                            l10n.identityValidTitle,
                            style: theme.textTheme.titleMedium,
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Text(student.fullName, style: theme.textTheme.titleLarge),
                      Text(student.universityId, style: theme.textTheme.bodyMedium),
                      const SizedBox(height: 12),
                      if (student.department != null)
                        Text('${l10n.departmentLabel}: ${student.department}'),
                      if (student.stage != null)
                        Text('${l10n.stageLabel}: ${student.stage}'),
                      if (student.group != null)
                        Text('${l10n.groupLabel}: ${student.group}'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                key: const Key('rescanIdentityButton'),
                onPressed: _rescan,
                icon: const Icon(Icons.qr_code_scanner),
                label: Text(l10n.identityVerifyButton),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
