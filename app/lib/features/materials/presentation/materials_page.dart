import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/platform/link_opener.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/materials_api.dart';
import 'offering_materials_page.dart';

/// مواد المقررات (نموذج الشاشة 6): قائمة المواد الدراسية للمستخدم،
/// والضغط على مادة يفتح ملفاتها وروابطها.
class MaterialsPage extends StatefulWidget {
  const MaterialsPage({
    super.key,
    required this.api,
    required this.session,
    this.opener,
  });

  final MaterialsApi api;
  final SessionController session;
  final LinkOpener? opener;

  @override
  State<MaterialsPage> createState() => _MaterialsPageState();
}

class _MaterialsPageState extends State<MaterialsPage> {
  bool _loading = true;
  String? _error;
  List<OfferingSummary> _offerings = const [];

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
      final offerings = await widget.api.myOfferings();
      if (!mounted) {
        return;
      }
      setState(() {
        _offerings = offerings;
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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.courseMaterialsTitle)),
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
                          key: const Key('materialsRetry'),
                          onPressed: _load,
                          icon: const Icon(Icons.refresh),
                          label: Text(l10n.retryButton),
                        ),
                      ],
                    ),
                  )
                : _offerings.isEmpty
                    ? Center(child: Text(l10n.noOfferings))
                    : ListView.separated(
                        padding: const EdgeInsets.all(12),
                        itemCount: _offerings.length,
                        separatorBuilder: (context, index) =>
                            const SizedBox(height: 8),
                        itemBuilder: (context, index) {
                          final offering = _offerings[index];
                          return _OfferingTile(
                            offering: offering,
                            onTap: () => Navigator.of(context).push(
                              MaterialPageRoute<void>(
                                builder: (_) => OfferingMaterialsPage(
                                  offering: offering,
                                  api: widget.api,
                                  session: widget.session,
                                  opener: widget.opener,
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

class _OfferingTile extends StatelessWidget {
  const _OfferingTile({required this.offering, required this.onTap});

  final OfferingSummary offering;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final meta = <String>[
      if (offering.instructorNameAr != null) offering.instructorNameAr!,
      '${l10n.stageLabel} ${offering.stage}',
      '${l10n.groupLabel} ${offering.groupName}',
      offering.kind == 'lab' ? l10n.sessionKindLab : l10n.sessionKindTheory,
    ].join(' · ');

    return Card(
      margin: EdgeInsets.zero,
      child: ListTile(
        key: Key('offeringTile-${offering.offeringId}'),
        onTap: onTap,
        leading: Icon(
          offering.kind == 'lab' ? Icons.science_outlined : Icons.menu_book_outlined,
          color: theme.colorScheme.primary,
        ),
        title: Text(offering.courseNameAr,
            maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text('${offering.courseCode} · $meta',
            maxLines: 2, overflow: TextOverflow.ellipsis),
        trailing: const Icon(Icons.chevron_left),
      ),
    );
  }
}
