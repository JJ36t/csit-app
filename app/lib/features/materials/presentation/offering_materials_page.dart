import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/platform/link_opener.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/materials_api.dart';

/// ملفات مادة واحدة: PDF برابط تنزيل موقّع، أو روابط فيديو/مراجع تُفتح خارجياً.
class OfferingMaterialsPage extends StatefulWidget {
  const OfferingMaterialsPage({
    super.key,
    required this.offering,
    required this.api,
    required this.session,
    this.opener,
  });

  final OfferingSummary offering;
  final MaterialsApi api;
  final SessionController session;
  final LinkOpener? opener;

  @override
  State<OfferingMaterialsPage> createState() => _OfferingMaterialsPageState();
}

class _OfferingMaterialsPageState extends State<OfferingMaterialsPage> {
  late final LinkOpener _opener = widget.opener ?? const UrlLauncherLinkOpener();

  bool _loading = true;
  String? _error;
  List<MaterialItem> _items = const [];

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
      final items = await widget.api.materials(widget.offering.offeringId);
      if (!mounted) {
        return;
      }
      setState(() {
        _items = items;
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

  Future<void> _open(MaterialItem item) async {
    final l10n = AppLocalizations.of(context)!;
    final target = item.downloadUrl != null
        ? absoluteApiUrl(item.downloadUrl!)
        : item.url;
    if (target == null) {
      return;
    }
    final opened = await _opener.open(Uri.parse(target));
    if (!opened && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.materialsLinkOpenFailed)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(widget.offering.courseNameAr)),
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
                          key: const Key('offeringMaterialsRetry'),
                          onPressed: _load,
                          icon: const Icon(Icons.refresh),
                          label: Text(l10n.retryButton),
                        ),
                      ],
                    ),
                  )
                : _items.isEmpty
                    ? Center(child: Text(l10n.courseMaterialsEmpty))
                    : ListView.separated(
                        padding: const EdgeInsets.all(12),
                        itemCount: _items.length,
                        separatorBuilder: (context, index) =>
                            const SizedBox(height: 8),
                        itemBuilder: (context, index) {
                          final item = _items[index];
                          return _MaterialTile(
                            item: item,
                            onOpen: () => _open(item),
                          );
                        },
                      ),
      ),
    );
  }
}

class _MaterialTile extends StatelessWidget {
  const _MaterialTile({required this.item, required this.onOpen});

  final MaterialItem item;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    final (icon, actionLabel) = switch (item.kind) {
      'pdf' => (Icons.picture_as_pdf_outlined, l10n.materialsDownload),
      'video_link' => (Icons.play_circle_outline, l10n.materialsOpenLink),
      _ => (Icons.link, l10n.materialsOpenLink),
    };
    final meta = <String>[
      if (item.weekNo != null) l10n.materialsWeek(item.weekNo!),
      if (item.fileSize != null) _sizeLabel(item.fileSize!),
      item.kind == 'pdf' ? 'PDF' : '',
    ].where((value) => value.isNotEmpty).join(' · ');

    return Card(
      margin: EdgeInsets.zero,
      child: ListTile(
        key: Key('materialTile-${item.materialId}'),
        leading: Icon(icon, color: theme.colorScheme.primary),
        title: Text(item.title, maxLines: 2, overflow: TextOverflow.ellipsis),
        subtitle: meta.isEmpty ? null : Text(meta),
        trailing: TextButton(
          key: Key('materialOpen-${item.materialId}'),
          onPressed: onOpen,
          child: Text(actionLabel),
        ),
      ),
    );
  }

  String _sizeLabel(int bytes) {
    if (bytes >= 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)}MB';
    }
    if (bytes >= 1024) {
      return '${(bytes / 1024).toStringAsFixed(0)}KB';
    }
    return '$bytes B';
  }
}
