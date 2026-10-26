import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/timetable_api.dart';

/// الجدول الأسبوعي (نموذج الشاشة 3): شرائح أيام + محاضرات اليوم المحدد،
/// مع تغييرات مؤرخة، وقراءة من ذاكرة محلية عند تعذر الشبكة.
class TimetablePage extends StatefulWidget {
  const TimetablePage({
    super.key,
    required this.api,
    required this.session,
    this.daysAhead = 14,
  });

  final TimetableApi api;
  final SessionController session;
  final int daysAhead;

  @override
  State<TimetablePage> createState() => _TimetablePageState();
}

class _TimetablePageState extends State<TimetablePage> {
  bool _loading = true;
  String? _error;
  TimetableData? _data;
  DateTime? _selectedDay;

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
    final today = toBaghdad(DateTime.now().toUtc());
    try {
      final data = await widget.api.load(
        from: today,
        to: today.add(Duration(days: widget.daysAhead)),
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _data = data;
        _loading = false;
        _selectedDay = _dayKey(_pickInitialDay(data, today));
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

  /// يوم البداية: اليوم إن كانت فيه محاضرات، وإلا أول يوم فيه محاضرات.
  DateTime _pickInitialDay(TimetableData data, DateTime today) {
    final todayKey = _dayKey(today);
    final hasToday = data.sessions
        .any((item) => _dayKey(toBaghdad(item.startsAt)) == todayKey);
    if (hasToday) {
      return today;
    }
    if (data.sessions.isEmpty) {
      return today;
    }
    final first = data.sessions
        .map((item) => toBaghdad(item.startsAt))
        .reduce((a, b) => a.isBefore(b) ? a : b);
    return first;
  }

  DateTime _dayKey(DateTime moment) =>
      DateTime.utc(moment.year, moment.month, moment.day);

  List<DateTime> _days(TimetableData data) {
    final keys = <DateTime>{};
    for (final item in data.sessions) {
      final local = toBaghdad(item.startsAt);
      keys.add(_dayKey(local));
    }
    final sorted = keys.toList()..sort();
    return sorted;
  }

  List<SessionItem> _sessionsOf(TimetableData data, DateTime day) => data.sessions
      .where((item) => _dayKey(toBaghdad(item.startsAt)) == day)
      .toList()
    ..sort((a, b) => a.startsAt.compareTo(b.startsAt));

  List<TimetableChange> _changesOf(TimetableData data, DateTime day) =>
      data.changes
          .where((change) => _dayKey(change.date) == day)
          .toList();

  String _weekdayLabel(AppLocalizations l10n, DateTime day) {
    switch (day.weekday) {
      case DateTime.monday:
        return l10n.weekdayMonday;
      case DateTime.tuesday:
        return l10n.weekdayTuesday;
      case DateTime.wednesday:
        return l10n.weekdayWednesday;
      case DateTime.thursday:
        return l10n.weekdayThursday;
      case DateTime.friday:
        return l10n.weekdayFriday;
      case DateTime.saturday:
        return l10n.weekdaySaturday;
      default:
        return l10n.weekdaySunday;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final data = _data;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.timetableTitle),
        actions: [
          IconButton(
            key: const Key('timetableRefresh'),
            tooltip: l10n.retryButton,
            onPressed: _loading ? null : _load,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null || data == null
                ? _ErrorView(
                    message: _error ?? l10n.unexpectedError,
                    retryLabel: l10n.retryButton,
                    onRetry: _load,
                  )
                : _content(l10n, data),
      ),
    );
  }

  Widget _content(AppLocalizations l10n, TimetableData data) {
    final days = _days(data);
    final selected = _selectedDay ?? _dayKey(toBaghdad(DateTime.now().toUtc()));
    final sessions = _sessionsOf(data, selected);
    final changes = _changesOf(data, selected);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (data.fromCache && data.fetchedAt != null)
          Container(
            key: const Key('timetableOfflineBanner'),
            width: double.infinity,
            margin: const EdgeInsets.fromLTRB(12, 8, 12, 0),
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xFFFBF0DF),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              l10n.timetableOffline(formatHm(data.fetchedAt!)),
              style: const TextStyle(color: Color(0xFF8A4B00)),
            ),
          ),
        if (days.isNotEmpty)
          SizedBox(
            height: 88,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              itemCount: days.length,
              separatorBuilder: (context, index) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final day = days[index];
                final isSelected = day == selected;
                return _DayChip(
                  key: Key('dayChip-${day.toIso8601String()}'),
                  weekday: _weekdayLabel(l10n, day),
                  dayNumber: toBaghdad(day).day.toString(),
                  selected: isSelected,
                  onTap: () => setState(() => _selectedDay = day),
                );
              },
            ),
          ),
        if (changes.isNotEmpty) _ChangesBanner(changes: changes),
        Expanded(
          child: sessions.isEmpty
              ? Center(child: Text(l10n.timetableEmpty))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.separated(
                    padding: const EdgeInsets.all(12),
                    itemCount: sessions.length,
                    separatorBuilder: (context, index) =>
                        const SizedBox(height: 8),
                    itemBuilder: (context, index) =>
                        _SessionTile(item: sessions[index]),
                  ),
                ),
        ),
      ],
    );
  }
}

class _DayChip extends StatelessWidget {
  const _DayChip({
    super.key,
    required this.weekday,
    required this.dayNumber,
    required this.selected,
    required this.onTap,
  });

  final String weekday;
  final String dayNumber;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: 66,
        padding: const EdgeInsets.symmetric(vertical: 6),
        decoration: BoxDecoration(
          color: selected ? theme.colorScheme.primary : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected ? theme.colorScheme.primary : const Color(0xFFE3E8EF),
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              weekday,
              style: theme.textTheme.labelSmall?.copyWith(
                color: selected ? Colors.white : theme.colorScheme.onSurface,
              ),
            ),
            Text(
              dayNumber,
              style: theme.textTheme.titleMedium?.copyWith(
                color: selected ? Colors.white : theme.colorScheme.onSurface,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ChangesBanner extends StatelessWidget {
  const _ChangesBanner({required this.changes});

  final List<TimetableChange> changes;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFFFBF0DF),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final change in changes)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Text(
                _describe(l10n, change),
                style: theme.textTheme.bodySmall
                    ?.copyWith(color: const Color(0xFF8A4B00)),
              ),
            ),
        ],
      ),
    );
  }

  String _describe(AppLocalizations l10n, TimetableChange change) {
    final label = switch (change.type) {
      'cancel' => l10n.changeCancelled,
      'extra' => l10n.changeExtra,
      _ => l10n.changeMoved,
    };
    final time = change.newStart == null ? '' : ' ${formatHm(change.newStart!)}';
    final reason = (change.reason == null || change.reason!.isEmpty)
        ? ''
        : ' — ${change.reason}';
    return '$label: ${change.courseNameAr}$time$reason';
  }
}

class _SessionTile extends StatelessWidget {
  const _SessionTile({required this.item});

  final SessionItem item;

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
    final meta = <String>[
      if (item.room != null && item.room!.isNotEmpty) item.room!,
      item.kind == 'lab' ? l10n.sessionKindLab : l10n.sessionKindTheory,
    ].join(' · ');

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  formatHm(item.startsAt),
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                Text(formatHm(item.endsAt), style: theme.textTheme.bodySmall),
              ],
            ),
            const SizedBox(width: 12),
            Container(width: 3, height: 40, color: statusColor),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.courseNameAr, style: theme.textTheme.titleSmall),
                  if (meta.isNotEmpty)
                    Text(meta, style: theme.textTheme.bodySmall),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
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

class _ErrorView extends StatelessWidget {
  const _ErrorView({
    required this.message,
    required this.retryLabel,
    required this.onRetry,
  });

  final String message;
  final String retryLabel;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(message, textAlign: TextAlign.center),
          const SizedBox(height: 12),
          FilledButton.tonalIcon(
            key: const Key('timetableRetry'),
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: Text(retryLabel),
          ),
        ],
      ),
    );
  }
}
