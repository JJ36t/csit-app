import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/notifications_api.dart';

/// صندوق الإشعارات: عدد غير المقروء، تعليم واحد بالنقر وتعليم الكل،
/// وسحب للتحديث، وحالة فراغ عربية.
class NotificationsPage extends StatefulWidget {
  const NotificationsPage({
    super.key,
    required this.api,
    required this.session,
  });

  final NotificationsApi api;
  final SessionController session;

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  bool _loading = true;
  bool _markingAll = false;
  String? _error;
  List<NotificationItem> _items = const [];
  int _unreadCount = 0;

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

  /// جلب الصندوق بلا شاشة تحميل كاملة — يُستخدم للتمرير للتحديث.
  Future<void> _fetch() async {
    try {
      final inbox = await widget.api.inbox();
      if (!mounted) {
        return;
      }
      setState(() {
        _items = inbox.items;
        _unreadCount = inbox.unreadCount;
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

  Future<void> _markRead(NotificationItem item) async {
    final messenger = ScaffoldMessenger.of(context);
    final l10n = AppLocalizations.of(context)!;
    try {
      await widget.api.markRead(item.notificationId);
      if (!mounted) {
        return;
      }
      setState(() {
        _items = [
          for (final entry in _items)
            entry.notificationId == item.notificationId
                ? entry.copyWith(isRead: true)
                : entry,
        ];
        _unreadCount = _countUnread(_items);
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

  Future<void> _markAllRead() async {
    final messenger = ScaffoldMessenger.of(context);
    final l10n = AppLocalizations.of(context)!;
    setState(() => _markingAll = true);
    try {
      await widget.api.markAllRead();
      if (!mounted) {
        return;
      }
      setState(() {
        _items = [
          for (final entry in _items) entry.copyWith(isRead: true),
        ];
        _unreadCount = 0;
      });
      messenger.showSnackBar(SnackBar(content: Text(l10n.markAllReadDone)));
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      messenger.showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    } finally {
      if (mounted) {
        setState(() => _markingAll = false);
      }
    }
  }

  int _countUnread(List<NotificationItem> items) =>
      items.where((item) => !item.isRead).length;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.notificationsTitle),
        actions: [
          IconButton(
            key: const Key('markAllReadButton'),
            tooltip: l10n.markAllReadButton,
            onPressed: _unreadCount == 0 || _markingAll ? null : _markAllRead,
            icon: const Icon(Icons.done_all),
          ),
        ],
      ),
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
                          key: const Key('notificationsRetry'),
                          onPressed: _load,
                          icon: const Icon(Icons.refresh),
                          label: Text(l10n.retryButton),
                        ),
                      ],
                    ),
                  )
                : RefreshIndicator(
                    onRefresh: _fetch,
                    child: ListView(
                      padding: const EdgeInsets.all(12),
                      children: [
                        if (_unreadCount > 0)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: Align(
                              alignment: AlignmentDirectional.centerStart,
                              child: Container(
                                key: const Key('notificationsUnreadChip'),
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 10,
                                  vertical: 4,
                                ),
                                decoration: BoxDecoration(
                                  color:
                                      Theme.of(context).colorScheme.primaryContainer,
                                  borderRadius: BorderRadius.circular(999),
                                ),
                                child: Text(
                                  l10n.notificationsUnread(_unreadCount),
                                  style: Theme.of(context)
                                      .textTheme
                                      .labelSmall
                                      ?.copyWith(
                                        color: Theme.of(context)
                                            .colorScheme
                                            .onPrimaryContainer,
                                        fontWeight: FontWeight.bold,
                                      ),
                                ),
                              ),
                            ),
                          ),
                        if (_items.isEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 32),
                            child: Text(
                              l10n.notificationsEmpty,
                              key: const Key('notificationsEmpty'),
                              textAlign: TextAlign.center,
                            ),
                          )
                        else
                          ..._items.map(
                            (item) => Padding(
                              padding: const EdgeInsets.only(bottom: 8),
                              child: _NotificationTile(
                                item: item,
                                onTap: item.isRead
                                    ? null
                                    : () => _markRead(item),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  const _NotificationTile({required this.item, required this.onTap});

  final NotificationItem item;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final createdAt = item.createdAt;

    return Card(
      margin: EdgeInsets.zero,
      child: ListTile(
        key: Key('notificationTile-${item.notificationId}'),
        onTap: onTap,
        leading: Icon(
          _iconFor(item.type),
          color: item.isRead
              ? theme.colorScheme.outline
              : theme.colorScheme.primary,
        ),
        title: Text(
          item.title,
          style: item.isRead
              ? theme.textTheme.bodyMedium
              : theme.textTheme.titleSmall,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(item.body),
            if (createdAt != null)
              Text(
                formatYmdHm(createdAt),
                style: theme.textTheme.labelSmall,
              ),
          ],
        ),
        trailing: item.isRead
            ? null
            : Container(
                key: Key('notificationUnread-${item.notificationId}'),
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary,
                  shape: BoxShape.circle,
                ),
              ),
      ),
    );
  }

  IconData _iconFor(String type) {
    switch (type) {
      case 'announcement':
        return Icons.campaign_outlined;
      case 'attendance':
        return Icons.fact_check_outlined;
      default:
        return Icons.notifications_none;
    }
  }
}
