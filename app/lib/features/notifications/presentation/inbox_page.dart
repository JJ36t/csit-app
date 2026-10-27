import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/notifications_api.dart';

/// صندوق الإشعارات داخل التطبيق — يبقى المرجع المضمون حتى لو تعطّل الدفع.
class InboxPage extends StatefulWidget {
  const InboxPage({super.key, required this.api, required this.session});

  final NotificationsApi api;
  final SessionController session;

  @override
  State<InboxPage> createState() => _InboxPageState();
}

class _InboxPageState extends State<InboxPage> {
  bool _loading = true;
  String? _error;
  List<AppNotification> _items = const [];
  int _unread = 0;

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
      final data = await widget.api.load();
      if (!mounted) {
        return;
      }
      setState(() {
        _items = data.items;
        _unread = data.unreadCount;
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

  Future<void> _markAll() async {
    final l10n = AppLocalizations.of(context)!;
    try {
      await widget.api.markAllRead();
      if (!mounted) {
        return;
      }
      setState(() {
        _items = _items
            .map(
              (row) => AppNotification(
                id: row.id,
                type: row.type,
                title: row.title,
                body: row.body,
                isRead: true,
                createdAt: row.createdAt,
                data: row.data,
              ),
            )
            .toList();
        _unread = 0;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.markAllRead)),
      );
    } catch (_) {
      // تجاهل: يعاد المحاولة عند السحب
    }
  }

  Future<void> _open(AppNotification item) async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(item.title, style: Theme.of(context).textTheme.titleLarge),
              if (item.createdAt != null) ...[
                const SizedBox(height: 4),
                Text(
                  formatHm(item.createdAt!),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
              const SizedBox(height: 16),
              Text(item.body, style: Theme.of(context).textTheme.bodyLarge),
            ],
          ),
        ),
      ),
    );
    if (item.isRead) {
      return;
    }
    try {
      await widget.api.markRead(item.id);
      if (!mounted) {
        return;
      }
      setState(() {
        _items = _items
            .map(
              (row) => row.id == item.id
                  ? AppNotification(
                      id: row.id,
                      type: row.type,
                      title: row.title,
                      body: row.body,
                      isRead: true,
                      createdAt: row.createdAt,
                      data: row.data,
                    )
                  : row,
            )
            .toList();
        _unread = (_unread - 1).clamp(0, 9999);
      });
    } catch (_) {
      // لا نعطّل القراءة لفشل تعليم الإشعار
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.inboxTitle),
        actions: [
          if (_unread > 0)
            IconButton(
              key: const Key('markAllReadButton'),
              tooltip: l10n.markAllRead,
              onPressed: _markAll,
              icon: const Icon(Icons.done_all),
            ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? ListView(
                    padding: const EdgeInsets.all(24),
                    children: [
                      Text(_error!, textAlign: TextAlign.center),
                      const SizedBox(height: 12),
                      FilledButton(onPressed: _load, child: Text(l10n.retryButton)),
                    ],
                  )
                : _items.isEmpty
                    ? ListView(
                        padding: const EdgeInsets.all(24),
                        children: [
                          const SizedBox(height: 60),
                          Icon(Icons.notifications_none,
                              size: 56, color: theme.colorScheme.outline),
                          const SizedBox(height: 12),
                          Text(l10n.inboxEmpty, textAlign: TextAlign.center),
                        ],
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: _items.length,
                        itemBuilder: (context, index) {
                          final item = _items[index];
                          return Card(
                            child: ListTile(
                              key: Key('notification-${item.id}'),
                              leading: Icon(
                                item.isRead
                                    ? Icons.mark_email_read_outlined
                                    : Icons.mark_email_unread_outlined,
                                color: item.isRead ? theme.colorScheme.outline : theme.colorScheme.primary,
                              ),
                              title: Text(
                                item.title,
                                style: TextStyle(
                                  fontWeight:
                                      item.isRead ? FontWeight.normal : FontWeight.bold,
                                ),
                              ),
                              subtitle: Text(
                                item.body,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                              trailing: item.createdAt == null
                                  ? null
                                  : Text(
                                      formatHm(item.createdAt!),
                                      style: theme.textTheme.bodySmall,
                                    ),
                              onTap: () => _open(item),
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}
