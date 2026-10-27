import 'dart:async';

import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../../core/network/api_client.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/identity_api.dart';

/// بطاقة الطالب الرقمية: رمز QR موقّع قصير العمر يتجدد تلقائياً عند الانتهاء.
class IdentityCardPage extends StatefulWidget {
  const IdentityCardPage({super.key, required this.api, required this.session});

  final IdentityApi api;
  final SessionController session;

  @override
  State<IdentityCardPage> createState() => _IdentityCardPageState();
}

class _IdentityCardPageState extends State<IdentityCardPage> {
  IdentityCard? _card;
  String? _error;
  bool _loading = true;
  Timer? _timer;
  int _secondsLeft = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final card = await widget.api.myCard();
      if (!mounted) {
        return;
      }
      setState(() {
        _card = card;
        _loading = false;
        _secondsLeft = _remaining(card);
      });
      _startTimer();
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
        _loading = false;
      });
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() {
        _error = AppLocalizations.of(context)!.unexpectedError;
        _loading = false;
      });
    }
  }

  int _remaining(IdentityCard card) {
    final diff = card.expiresAt.difference(DateTime.now().toUtc()).inSeconds;
    return diff < 0 ? 0 : diff;
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      final card = _card;
      if (card == null || !mounted) {
        return;
      }
      final remaining = _remaining(card);
      setState(() => _secondsLeft = remaining);
      if (remaining <= 0) {
        timer.cancel();
        _load(); // تجديد تلقائي بلا تدخل الطالب
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final card = _card;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.identityTitle),
        actions: [
          IconButton(
            tooltip: l10n.identityRefreshButton,
            onPressed: _loading ? null : _load,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(_error!, textAlign: TextAlign.center),
                        const SizedBox(height: 12),
                        FilledButton(onPressed: _load, child: Text(l10n.retryButton)),
                      ],
                    ),
                  ),
                )
              : ListView(
                  padding: const EdgeInsets.all(20),
                  children: [
                    if (card != null) ...[
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            children: [
                              Text(
                                card.profile.fullName,
                                style: theme.textTheme.titleLarge,
                                textAlign: TextAlign.center,
                              ),
                              Text(
                                card.profile.universityId,
                                style: theme.textTheme.bodyMedium,
                              ),
                              const SizedBox(height: 16),
                              Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(16),
                                ),
                                child: QrImageView(
                                  data: card.card,
                                  version: QrVersions.auto,
                                  size: 240,
                                  backgroundColor: Colors.white,
                                ),
                              ),
                              const SizedBox(height: 12),
                              LinearProgressIndicator(
                                value: card.ttlSeconds == 0
                                    ? 0
                                    : (_secondsLeft / card.ttlSeconds).clamp(0.0, 1.0),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _secondsLeft > 0
                                    ? l10n.identityValidFor(_secondsLeft)
                                    : l10n.identityExpiredError,
                                style: theme.textTheme.bodySmall,
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        l10n.identityCardNote,
                        textAlign: TextAlign.center,
                        style: theme.textTheme.bodySmall,
                      ),
                      const SizedBox(height: 16),
                      if (card.profile.department != null)
                        _InfoRow(
                          icon: Icons.account_tree_outlined,
                          label: l10n.departmentLabel,
                          value: card.profile.department!,
                        ),
                      if (card.profile.stage != null)
                        _InfoRow(
                          icon: Icons.layers_outlined,
                          label: l10n.stageLabel,
                          value: '${card.profile.stage}',
                        ),
                      if (card.profile.group != null)
                        _InfoRow(
                          icon: Icons.groups_outlined,
                          label: l10n.groupLabel,
                          value: card.profile.group!,
                        ),
                    ],
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      key: const Key('refreshIdentityCard'),
                      onPressed: _load,
                      icon: const Icon(Icons.autorenew),
                      label: Text(l10n.identityRefreshButton),
                    ),
                  ],
                ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.icon, required this.label, required this.value});

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: Icon(icon),
        title: Text(label),
        subtitle: Text(value),
      ),
    );
  }
}
