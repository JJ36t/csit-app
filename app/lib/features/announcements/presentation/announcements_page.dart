import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/announcements_api.dart';
import 'announcement_detail_page.dart';

/// الإعلانات الموجّهة للمستخدم: قائمة بشرائح التثبيت/الأولوية،
/// وسحب للتحديث، وفتح الإعلان يعرض نصه كاملاً ويعلّمه مقروءاً.
class AnnouncementsPage extends StatefulWidget {
  const AnnouncementsPage({
    super.key,
    required this.api,
    required this.session,
  });

  final AnnouncementsApi api;
  final SessionController session;

  @override
  State<AnnouncementsPage> createState() => _AnnouncementsPageState();
}

class _AnnouncementsPageState extends State<AnnouncementsPage> {
  bool _loading = true;
  String? _error;
  List<AnnouncementItem> _items = const [];

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
    await _fetch();
  }

  /// جلب القائمة بلا شاشة تحميل كاملة — يُستخدم للتمرير للتحديث.
  Future<void> _fetch() async {
    try {
      final items = await widget.api.feed();
      if (!mounted) {
        return;
      }
      setState(() {
        _items = items;
        _error = null;
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
        _error =
            error.messageAr ?? AppLocalizations.of(context)!.unexpectedError;
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

  /// فتح الإعلان يعلّمه مقروءاً على الخادم ثم يحدّث شارة «غير مقروء» محلياً.
  Future<void> _open(AnnouncementItem item) async {
    final messenger = ScaffoldMessenger.of(context);
    final l10n = AppLocalizations.of(context)!;
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => AnnouncementDetailPage(item: item),
      ),
    );
    if (item.isRead) {
      return;
    }
    try {
      await widget.api.markRead(item.announcementId);
      if (!mounted) {
        return;
      }
      setState(() {
        _items = [
          for (final entry in _items)
            entry.announcementId == item.announcementId
                ? entry.copyWith(isRead: true)
                : entry,
        ];
      });
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      messenger.showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.announcementsTitle)),
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
                          key: const Key('announcementsRetry'),
                          onPressed: _load,
                          icon: const Icon(Icons.refresh),
                          label: Text(l10n.retryButton),
                        ),
                      ],
                    ),
                  )
                : RefreshIndicator(
                    onRefresh: _fetch,
                    child: _items.isEmpty
                        ? ListView(
                            padding: const EdgeInsets.all(24),
                            children: [
                              Text(
                                l10n.announcementsEmpty,
                                key: const Key('announcementsEmpty'),
                                textAlign: TextAlign.center,
                              ),
                            ],
                          )
                        : ListView.separated(
                            padding: const EdgeInsets.all(12),
                            itemCount: _items.length,
                            separatorBuilder: (context, index) =>
                                const SizedBox(height: 10),
                            itemBuilder: (context, index) {
                              final item = _items[index];
                              return _AnnouncementCard(
                                item: item,
                                onTap: () => _open(item),
                              );
                            },
                          ),
                  ),
      ),
    );
  }
}

class _AnnouncementCard extends StatelessWidget {
  const _AnnouncementCard({required this.item, required this.onTap});

  final AnnouncementItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final published = item.publishedAt;

    return Card(
      margin: EdgeInsets.zero,
      child: InkWell(
        key: Key('announcementTile-${item.announcementId}'),
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (!item.isRead)
                    Container(
                      key: Key('announcementUnread-${item.announcementId}'),
                      width: 8,
                      height: 8,
                      margin: const EdgeInsetsDirectional.only(end: 6, top: 6),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primary,
                        shape: BoxShape.circle,
                      ),
                    ),
                  Expanded(
                    child: Text(
                      item.title,
                      style: theme.textTheme.titleSmall,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                item.body,
                style: theme.textTheme.bodySmall,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              if (item.pinned || item.isHighPriority || published != null) ...[
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    if (item.pinned)
                      _StatusChip(
                        key: Key('announcementPinned-${item.announcementId}'),
                        label: l10n.announcementPinned,
                        background: theme.colorScheme.secondaryContainer,
                        foreground: theme.colorScheme.onSecondaryContainer,
                      ),
                    if (item.isHighPriority)
                      _StatusChip(
                        key: Key('announcementPriority-${item.announcementId}'),
                        label: l10n.announcementPriorityHigh,
                        background: theme.colorScheme.errorContainer,
                        foreground: theme.colorScheme.onErrorContainer,
                      ),
                    if (published != null)
                      Text(
                        formatYmdHm(published),
                        style: theme.textTheme.labelSmall,
                      ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// شريحة صغيرة للتثبيت أو الأولوية.
class _StatusChip extends StatelessWidget {
  const _StatusChip({
    super.key,
    required this.label,
    required this.background,
    required this.foreground,
  });

  final String label;
  final Color background;
  final Color foreground;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: theme.textTheme.labelSmall?.copyWith(
          color: foreground,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
