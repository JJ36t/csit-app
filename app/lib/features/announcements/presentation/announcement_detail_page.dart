import 'package:flutter/material.dart';

import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../data/announcements_api.dart';

/// نص الإعلان كاملاً مع شرائح التثبيت/الأولوية وتاريخ النشر.
class AnnouncementDetailPage extends StatelessWidget {
  const AnnouncementDetailPage({super.key, required this.item});

  final AnnouncementItem item;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final published = item.publishedAt;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.announcementsTitle)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              item.title,
              key: const Key('announcementDetailTitle'),
              style: theme.textTheme.titleLarge,
            ),
            if (item.pinned || item.isHighPriority || published != null) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  if (item.pinned) Text(l10n.announcementPinned),
                  if (item.isHighPriority)
                    Text(
                      l10n.announcementPriorityHigh,
                      style: TextStyle(color: theme.colorScheme.error),
                    ),
                  if (published != null)
                    Text(
                      formatYmdHm(published),
                      style: theme.textTheme.labelSmall,
                    ),
                ],
              ),
            ],
            const Divider(height: 24),
            Text(
              item.body,
              key: const Key('announcementDetailBody'),
              style: theme.textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }
}
