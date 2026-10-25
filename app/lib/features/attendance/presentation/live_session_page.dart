import 'dart:async';

import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../../core/network/api_client.dart';
import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/attendance_api.dart';
import '../data/qr_payload.dart';

/// حالة الحضور الفعّالة للطالب في القائمة (الترتيب يحدد العرض).
String effectiveStatus(LiveStudent student) {
  if (student.flagged) {
    return 'flagged';
  }
  if (student.status == null) {
    return 'unrecorded';
  }
  return student.status!;
}

/// قائمة الحاضرين اللحظية للتدريسي: عدّاد، رمز QR متجدد، فتح/إغلاق، وتصفية
/// (نموذج الشاشة 5). تقرأ `/sessions/{id}/live` وتحدّث نفسها دورياً.
class LiveSessionPage extends StatefulWidget {
  const LiveSessionPage({
    super.key,
    required this.summary,
    required this.api,
    required this.session,
    this.pollInterval = const Duration(seconds: 10),
  });

  final SessionSummary summary;
  final AttendanceApi api;
  final SessionController session;

  /// فترة التحديث الدوري؛ null يعطّله (الاختبارات).
  final Duration? pollInterval;

  @override
  State<LiveSessionPage> createState() => _LiveSessionPageState();
}

enum _RosterFilter { all, present, late, flagged, absent }

class _LiveSessionPageState extends State<LiveSessionPage> {
  LiveSessionData? _data;
  bool _loading = true;
  bool _acting = false;
  String? _error;
  _RosterFilter _filter = _RosterFilter.all;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _refresh() async {
    try {
      final data = await widget.api.liveSession(widget.summary.sessionId);
      if (!mounted) {
        return;
      }
      setState(() {
        _data = data;
        _loading = false;
        _error = null;
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
    } finally {
      _scheduleNext();
    }
  }

  void _scheduleNext() {
    _timer?.cancel();
    final interval = widget.pollInterval;
    if (interval == null || !mounted) {
      return;
    }
    _timer = Timer(interval, _refresh);
  }

  Future<void> _openSession() async {
    if (_acting) {
      return;
    }
    final l10n = AppLocalizations.of(context)!;
    setState(() => _acting = true);
    try {
      await widget.api.openSession(widget.summary.sessionId);
      await _refresh();
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      if (error.statusCode == 401) {
        widget.session.expire();
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    } finally {
      if (mounted) {
        setState(() => _acting = false);
      }
    }
  }

  Future<void> _confirmClose() async {
    if (_acting) {
      return;
    }
    final l10n = AppLocalizations.of(context)!;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(l10n.closeSessionConfirmTitle),
        content: Text(l10n.closeSessionConfirmBody),
        actions: [
          TextButton(
            key: const Key('closeCancel'),
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: Text(l10n.cancelButton),
          ),
          FilledButton(
            key: const Key('closeConfirm'),
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text(l10n.confirmButton),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) {
      return;
    }
    setState(() => _acting = true);
    try {
      final result =
          await widget.api.closeSession(widget.summary.sessionId);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.absentMarkedNote(result.absentMarked))),
      );
      await _refresh();
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      if (error.statusCode == 401) {
        widget.session.expire();
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    } finally {
      if (mounted) {
        setState(() => _acting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final data = _data;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.liveTitle)),
      body: SafeArea(
        child: _loading && data == null
            ? const Center(child: CircularProgressIndicator())
            : data == null
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(_error ?? l10n.unexpectedError,
                            textAlign: TextAlign.center),
                        const SizedBox(height: 12),
                        FilledButton.tonalIcon(
                          key: const Key('liveRetry'),
                          onPressed: _refresh,
                          icon: const Icon(Icons.refresh),
                          label: Text(l10n.retryButton),
                        ),
                      ],
                    ),
                  )
                : ListView(
                    padding: const EdgeInsets.all(12),
                    children: [
                      _HeaderCard(summary: widget.summary, status: data.status),
                      const SizedBox(height: 10),
                      _CounterCard(data: data),
                      if (data.isOpen && data.qr != null) ...[
                        const SizedBox(height: 10),
                        _QrCard(sessionId: data.sessionId, qr: data.qr!),
                      ],
                      if (data.status == 'scheduled') ...[
                        const SizedBox(height: 10),
                        _ActionCard(
                          hint: l10n.openSessionHint,
                          buttonKey: const Key('openSessionButton'),
                          buttonLabel: l10n.openSessionButton,
                          icon: Icons.play_arrow,
                          onPressed: _acting ? null : _openSession,
                        ),
                      ],
                      if (data.isOpen) ...[
                        const SizedBox(height: 10),
                        _ActionCard(
                          hint: l10n.closeSessionNote,
                          buttonKey: const Key('closeSessionButton'),
                          buttonLabel: l10n.closeSessionButton,
                          icon: Icons.stop_circle_outlined,
                          danger: true,
                          onPressed: _acting ? null : _confirmClose,
                        ),
                      ],
                      const SizedBox(height: 14),
                      _RosterCard(
                        data: data,
                        filter: _filter,
                        onFilterChanged: (value) =>
                            setState(() => _filter = value),
                      ),
                    ],
                  ),
      ),
    );
  }
}

class _HeaderCard extends StatelessWidget {
  const _HeaderCard({required this.summary, required this.status});

  final SessionSummary summary;
  final String status;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    final (statusLabel, statusColor) = switch (status) {
      'open' => (l10n.sessionStatusOpen, const Color(0xFF1B7A55)),
      'closed' => (l10n.sessionStatusClosed, const Color(0xFF5B6875)),
      'cancelled' => (l10n.sessionStatusCancelled, const Color(0xFFB3261E)),
      _ => (l10n.sessionStatusScheduled, theme.colorScheme.primary),
    };

    final metaParts = <String>[
      if (summary.room != null && summary.room!.isNotEmpty) summary.room!,
      '${formatHm(summary.startsAt)}–${formatHm(summary.endsAt)}',
    ];

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(summary.courseNameAr,
                      style: theme.textTheme.titleMedium),
                  if (metaParts.isNotEmpty)
                    Text(metaParts.join(' · '),
                        style: theme.textTheme.bodySmall),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: statusColor.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(
                statusLabel,
                style:
                    theme.textTheme.labelSmall?.copyWith(color: statusColor),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CounterCard extends StatelessWidget {
  const _CounterCard({required this.data});

  final LiveSessionData data;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    final total = data.students.length;
    final statuses = data.students.map(effectiveStatus).toList();
    final present = statuses.where((value) => value == 'present').length;
    final lateCount = statuses.where((value) => value == 'late').length;
    final flagged = statuses.where((value) => value == 'flagged').length;
    final absent = statuses
        .where((value) => value == 'unrecorded' || value == 'absent')
        .length;
    final percent = total == 0 ? 0 : ((present * 100) / total).round();

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(l10n.liveAttendance, style: theme.textTheme.labelMedium),
                Text(
                  l10n.percentValue(percent),
                  style: theme.textTheme.labelMedium
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              l10n.presentOfTotal(present, total),
              key: const Key('liveCounter'),
              style: theme.textTheme.titleLarge
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: total == 0 ? 0 : present / total,
                minHeight: 6,
              ),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 10,
              runSpacing: 4,
              children: [
                _CountChip(
                    label: l10n.lateCount(lateCount),
                    color: const Color(0xFF8A4B00)),
                _CountChip(
                    label: l10n.flaggedCount(flagged),
                    color: const Color(0xFFB3261E)),
                _CountChip(
                    label: l10n.absentCount(absent),
                    color: const Color(0xFF5B6875)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _CountChip extends StatelessWidget {
  const _CountChip({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(label,
            style: theme.textTheme.bodySmall?.copyWith(color: color)),
      ],
    );
  }
}

class _QrCard extends StatelessWidget {
  const _QrCard({required this.sessionId, required this.qr});

  final String sessionId;
  final LiveQr qr;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          children: [
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: theme.colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(
                l10n.qrRenewsChip,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onPrimaryContainer,
                ),
              ),
            ),
            const SizedBox(height: 10),
            // محتوى الرمز: معرّف الجلسة + الرمز المتجدد — يقرؤه تطبيق الطالب.
            QrImageView(
              key: const Key('qrView'),
              data: QrPayload(sessionId: sessionId, token: qr.token).encode(),
              version: QrVersions.auto,
              size: 220,
              padding: const EdgeInsets.all(8),
              backgroundColor: Colors.white,
            ),
          ],
        ),
      ),
    );
  }
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({
    required this.hint,
    required this.buttonKey,
    required this.buttonLabel,
    required this.icon,
    required this.onPressed,
    this.danger = false,
  });

  final String hint;
  final Key buttonKey;
  final String buttonLabel;
  final IconData icon;
  final VoidCallback? onPressed;
  final bool danger;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Expanded(child: Text(hint, style: theme.textTheme.bodySmall)),
            const SizedBox(width: 8),
            danger
                ? OutlinedButton.icon(
                    key: buttonKey,
                    onPressed: onPressed,
                    icon: Icon(icon, color: const Color(0xFFB3261E)),
                    label: Text(
                      buttonLabel,
                      style: const TextStyle(color: Color(0xFFB3261E)),
                    ),
                  )
                : FilledButton.icon(
                    key: buttonKey,
                    onPressed: onPressed,
                    icon: Icon(icon),
                    label: Text(buttonLabel),
                  ),
          ],
        ),
      ),
    );
  }
}

class _RosterCard extends StatelessWidget {
  const _RosterCard({
    required this.data,
    required this.filter,
    required this.onFilterChanged,
  });

  final LiveSessionData data;
  final _RosterFilter filter;
  final ValueChanged<_RosterFilter> onFilterChanged;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    final statuses = data.students.map(effectiveStatus).toList();
    final present = statuses.where((value) => value == 'present').length;
    final lateCount = statuses.where((value) => value == 'late').length;
    final flagged = statuses.where((value) => value == 'flagged').length;
    final absent = statuses
        .where((value) => value == 'unrecorded' || value == 'absent')
        .length;

    final visible = data.students.where((student) {
      final value = effectiveStatus(student);
      return switch (filter) {
        _RosterFilter.all => true,
        _RosterFilter.present => value == 'present',
        _RosterFilter.late => value == 'late',
        _RosterFilter.flagged => value == 'flagged',
        _RosterFilter.absent =>
          value == 'unrecorded' || value == 'absent',
      };
    }).toList();

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 8,
              children: [
                _FilterChip(
                  label: '${l10n.filterAll} (${data.students.length})',
                  selected: filter == _RosterFilter.all,
                  onTap: () => onFilterChanged(_RosterFilter.all),
                ),
                _FilterChip(
                  label: '${l10n.presentStatus} ($present)',
                  selected: filter == _RosterFilter.present,
                  onTap: () => onFilterChanged(_RosterFilter.present),
                ),
                _FilterChip(
                  label: '${l10n.lateStatus} ($lateCount)',
                  selected: filter == _RosterFilter.late,
                  onTap: () => onFilterChanged(_RosterFilter.late),
                ),
                _FilterChip(
                  label: '${l10n.flaggedStatus} ($flagged)',
                  selected: filter == _RosterFilter.flagged,
                  onTap: () => onFilterChanged(_RosterFilter.flagged),
                ),
                _FilterChip(
                  label: '${l10n.absentStatus} ($absent)',
                  selected: filter == _RosterFilter.absent,
                  onTap: () => onFilterChanged(_RosterFilter.absent),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (visible.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Text(
                  l10n.noStudentsInFilter,
                  textAlign: TextAlign.center,
                ),
              )
            else
              ...visible.map((student) => _RosterTile(student: student)),
          ],
        ),
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) => onTap(),
      visualDensity: VisualDensity.compact,
    );
  }
}

class _RosterTile extends StatelessWidget {
  const _RosterTile({required this.student});

  final LiveStudent student;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final status = effectiveStatus(student);

    final (label, color) = switch (status) {
      'flagged' => (l10n.flaggedStatus, const Color(0xFFB3261E)),
      'late' => (l10n.lateStatus, const Color(0xFF8A4B00)),
      'present' => (l10n.presentStatus, const Color(0xFF1B7A55)),
      'excused' => (l10n.excusedStatus, theme.colorScheme.primary),
      _ => (l10n.absentStatus, const Color(0xFF5B6875)),
    };
    final meta = status == 'unrecorded' || status == 'absent'
        ? l10n.notRecordedStatus
        : student.universityId;

    return ListTile(
      contentPadding: EdgeInsets.zero,
      dense: true,
      leading: CircleAvatar(
        radius: 16,
        child: Text(
          student.fullNameAr.isNotEmpty
              ? student.fullNameAr.substring(0, 1)
              : '?',
          style: theme.textTheme.labelMedium,
        ),
      ),
      title: Text(student.fullNameAr, maxLines: 1,
          overflow: TextOverflow.ellipsis),
      subtitle: Text(meta),
      trailing: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(
          label,
          style: theme.textTheme.labelSmall?.copyWith(color: color),
        ),
      ),
    );
  }
}
