import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/attendance_api.dart';
import 'live_session_page.dart';

/// حصص التدريسي اليوم — يختار جلسة لفتحها ومتابعة حاضرينها (نموذج الشاشة 5).
class SessionsPage extends StatefulWidget {
  const SessionsPage({
    super.key,
    required this.api,
    required this.session,
    this.pollInterval = const Duration(seconds: 10),
  });

  final AttendanceApi api;
  final SessionController session;

  /// فترة تحديث القائمة اللحظية؛ null في الاختبارات لتعطيل المؤقت.
  final Duration? pollInterval;

  @override
  State<SessionsPage> createState() => _SessionsPageState();
}

class _SessionsPageState extends State<SessionsPage> {
  bool _loading = true;
  String? _error;
  List<SessionSummary> _sessions = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final sessions = await widget.api.mySessions();
      if (!mounted) {
        return;
      }
      final now = DateTime.now().toUtc();
      setState(() {
        _sessions = sessions
            .where((item) => isSameBaghdadDay(now, item.startsAt))
            .toList()
          ..sort((a, b) => a.startsAt.compareTo(b.startsAt));
        _loading = false;
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
        _error = error.messageAr ??
            AppLocalizations.of(context)!.unexpectedError;
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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.todaySessionsTitle)),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(_error!, textAlign: TextAlign.center),
                        const SizedBox(height: 12),
                        FilledButton.tonalIcon(
                          key: const Key('sessionsRetry'),
                          onPressed: _load,
                          icon: const Icon(Icons.refresh),
                          label: Text(l10n.retryButton),
                        ),
                      ],
                    ),
                  )
                : _sessions.isEmpty
                    ? Center(child: Text(l10n.noSessionsToday))
                    : ListView.separated(
                        padding: const EdgeInsets.all(12),
                        itemCount: _sessions.length,
                        separatorBuilder: (context, index) => const SizedBox(height: 8),
                        itemBuilder: (context, index) {
                          final item = _sessions[index];
                          return _SessionTile(
                            item: item,
                            onTap: () => Navigator.of(context).push(
                              MaterialPageRoute<void>(
                                builder: (_) => LiveSessionPage(
                                  summary: item,
                                  api: widget.api,
                                  session: widget.session,
                                  pollInterval: widget.pollInterval,
                                ),
                              ),
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}

class _SessionTile extends StatelessWidget {
  const _SessionTile({required this.item, required this.onTap});

  final SessionSummary item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    final (statusLabel, statusColor) = switch (item.status) {
      'open' => (l10n.sessionStatusOpen, const Color(0xFF1B7A55)),
      'closed' => (l10n.sessionStatusClosed, const Color(0xFF5B6875)),
      'cancelled' => (l10n.sessionStatusCancelled, const Color(0xFFB3261E)),
      _ => (l10n.sessionStatusScheduled, theme.colorScheme.primary),
    };

    final metaParts = <String>[
      if (item.room != null && item.room!.isNotEmpty) item.room!,
      item.kind == 'lab' ? l10n.sessionKindLab : l10n.sessionKindTheory,
      '${formatHm(item.startsAt)}–${formatHm(item.endsAt)}',
    ];

    return Card(
      margin: EdgeInsets.zero,
      child: ListTile(
        key: Key('sessionTile-${item.sessionId}'),
        onTap: onTap,
        leading: Icon(
          item.kind == 'lab' ? Icons.science_outlined : Icons.menu_book_outlined,
          color: theme.colorScheme.primary,
        ),
        title: Text(item.courseNameAr,
            maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text(metaParts.join(' · ')),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: statusColor.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(999),
          ),
          child: Text(
            statusLabel,
            style: theme.textTheme.labelSmall?.copyWith(color: statusColor),
          ),
        ),
      ),
    );
  }
}
