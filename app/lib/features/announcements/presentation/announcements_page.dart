import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/announcements_api.dart';

/// الإعلانات الموجّهة للمستخدم: مثبّتة أولاً، مع علامة «مقروء» ونسخة محفوظة
/// تُعرض عند تعذر الاتصال (وضع بلا إنترنت).
class AnnouncementsPage extends StatefulWidget {
  const AnnouncementsPage({super.key, required this.api, required this.session});

  final AnnouncementsApi api;
  final SessionController session;

  @override
  State<AnnouncementsPage> createState() => _AnnouncementsPageState();
}

class _AnnouncementsPageState extends State<AnnouncementsPage> {
  bool _loading = true;
  String? _error;
  AnnouncementsData? _data;

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
        _data = data;
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

  Future<void> _open(AnnouncementItem item) async {
    // نعلّم المقروء قبل فتح النافذة كي ينطفئ مؤشر «جديد» فوراً
    if (!item.isRead) {
      try {
        await widget.api.markRead(item.id);
        if (mounted) {
          setState(() {
            _data = AnnouncementsData(
              items: _data!.items
                  .map((row) => row.id == item.id ? row.copyWith(isRead: true) : row)
                  .toList(),
              fetchedAt: _data!.fetchedAt,
              fromCache: _data!.fromCache,
            );
          });
        }
      } catch (_) {
        // الفشل لا يمنع القراءة — تُعلَّم لاحقاً عند أول اتصال ناجح
      }
    }
    if (!mounted) {
      return;
    }
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.title, style: Theme.of(context).textTheme.titleLarge),
                if (item.publishedAt != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    formatHm(item.publishedAt!),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
                const SizedBox(height: 16),
                Text(item.body, style: Theme.of(context).textTheme.bodyLarge),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final items = _data?.items ?? const <AnnouncementItem>[];

    return Scaffold(
      appBar: AppBar(title: Text(l10n.announcementsTitle)),
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
                : items.isEmpty
                    ? ListView(
                        padding: const EdgeInsets.all(24),
                        children: [
                          const SizedBox(height: 60),
                          Icon(Icons.campaign_outlined,
                              size: 56, color: Theme.of(context).colorScheme.outline),
                          const SizedBox(height: 12),
                          Text(l10n.announcementsEmpty, textAlign: TextAlign.center),
                        ],
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: items.length + (_data!.fromCache ? 1 : 0),
                        itemBuilder: (context, index) {
                          if (_data!.fromCache && index == 0) {
                            return _OfflineBanner(fetchedAt: _data!.fetchedAt);
                          }
                          final item = items[index - (_data!.fromCache ? 1 : 0)];
                          return Card(
                            child: ListTile(
                              key: Key('announcement-${item.id}'),
                              leading: Icon(
                                item.pinned
                                    ? Icons.push_pin_outlined
                                    : item.isHighPriority
                                        ? Icons.priority_high
                                        : Icons.campaign_outlined,
                                color: item.isHighPriority
                                    ? Theme.of(context).colorScheme.error
                                    : null,
                              ),
                              title: Row(
                                children: [
                                  Expanded(child: Text(item.title)),
                                  if (!item.isRead)
                                    Container(
                                      width: 8,
                                      height: 8,
                                      decoration: BoxDecoration(
                                        color: Theme.of(context).colorScheme.primary,
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                ],
                              ),
                              subtitle: Text(
                                item.body,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                              trailing: const Icon(Icons.chevron_left),
                              onTap: () => _open(item),
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}

class _OfflineBanner extends StatelessWidget {
  const _OfflineBanner({this.fetchedAt});

  final DateTime? fetchedAt;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final time = fetchedAt == null ? '' : formatHm(fetchedAt!);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.secondaryContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const Icon(Icons.cloud_off_outlined, size: 18),
          const SizedBox(width: 8),
          Expanded(child: Text(l10n.dataFromCache(time))),
        ],
      ),
    );
  }
}
