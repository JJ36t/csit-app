import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/network/api_client.dart';
import '../../../core/platform/link_opener.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/excuses_api.dart';

/// الأعذار: شاشة الطالب (قائمة + رفع عذر) أو شاشة المراجعة للتدريسي.
class ExcusesPage extends StatefulWidget {
  const ExcusesPage({
    super.key,
    required this.api,
    required this.session,
    this.reviewMode = false,
  });

  final ExcusesApi api;
  final SessionController session;
  final bool reviewMode;

  @override
  State<ExcusesPage> createState() => _ExcusesPageState();
}

class _ExcusesPageState extends State<ExcusesPage> {
  bool _loading = true;
  String? _error;
  List<ExcuseItem> _items = const [];
  int _pending = 0;

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
      if (widget.reviewMode) {
        final queue = await widget.api.reviewQueue();
        if (!mounted) {
          return;
        }
        setState(() {
          _items = queue.items;
          _pending = queue.pendingTotal;
          _loading = false;
        });
      } else {
        final items = await widget.api.myExcuses();
        if (!mounted) {
          return;
        }
        setState(() {
          _items = items;
          _loading = false;
        });
      }
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

  Future<void> _newExcuse() async {
    final created = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => NewExcusePage(api: widget.api, session: widget.session),
      ),
    );
    if (created == true) {
      await _load();
    }
  }

  Future<void> _withdraw(ExcuseItem item) async {
    final l10n = AppLocalizations.of(context)!;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.excuseWithdraw),
        content: Text(item.courseName),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.cancelButton),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.confirmButton),
          ),
        ],
      ),
    );
    if (confirmed != true) {
      return;
    }
    try {
      await widget.api.withdraw(item.id);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.excuseWithdrawn)),
      );
      await _load();
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    }
  }

  Future<void> _review(ExcuseItem item, {required bool approve}) async {
    final l10n = AppLocalizations.of(context)!;
    final controller = TextEditingController();
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(approve ? l10n.excuseApprove : l10n.excuseReject),
        content: TextField(
          controller: controller,
          maxLines: 3,
          decoration: InputDecoration(
            labelText: l10n.excuseReviewNote,
            hintText: l10n.excuseReviewNoteHint,
            border: const OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.cancelButton),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.confirmButton),
          ),
        ],
      ),
    );
    if (accepted != true) {
      return;
    }
    try {
      await widget.api.review(item.id, approve: approve, note: controller.text);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.excuseReviewed)),
      );
      await _load();
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    }
  }

  Future<void> _openAttachment(ExcuseAttachment attachment) async {
    final l10n = AppLocalizations.of(context)!;
    final ok = await const UrlLauncherLinkOpener()
        .open(Uri.parse(absoluteApiUrl(attachment.downloadUrl)));
    if (!ok && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.materialsLinkOpenFailed)),
      );
    }
  }

  String _statusLabel(AppLocalizations l10n, String status) => switch (status) {
        'approved' => l10n.excuseStatusApproved,
        'rejected' => l10n.excuseStatusRejected,
        _ => l10n.excuseStatusPending,
      };

  Color _statusColor(BuildContext context, String status) {
    final scheme = Theme.of(context).colorScheme;
    return switch (status) {
      'approved' => scheme.primary,
      'rejected' => scheme.error,
      _ => scheme.tertiary,
    };
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.reviewMode ? l10n.excuseReviewTitle : l10n.excusesTitle),
        actions: [
          if (widget.reviewMode && _pending > 0)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Center(child: Text(l10n.excusePendingCount(_pending))),
            ),
        ],
      ),
      floatingActionButton: widget.reviewMode
          ? null
          : FloatingActionButton.extended(
              key: const Key('newExcuseButton'),
              onPressed: _newExcuse,
              icon: const Icon(Icons.add),
              label: Text(l10n.excuseNewTitle),
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
                          Icon(Icons.assignment_late_outlined,
                              size: 56, color: theme.colorScheme.outline),
                          const SizedBox(height: 12),
                          Text(
                            widget.reviewMode ? l10n.excuseReviewEmpty : l10n.excusesEmpty,
                            textAlign: TextAlign.center,
                          ),
                        ],
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(12, 12, 12, 96),
                        itemCount: _items.length,
                        itemBuilder: (context, index) {
                          final item = _items[index];
                          return Card(
                            child: Padding(
                              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          '${item.courseName} · ${item.courseCode}',
                                          style: theme.textTheme.titleSmall,
                                        ),
                                      ),
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 10, vertical: 4),
                                        decoration: BoxDecoration(
                                          color: _statusColor(context, item.status)
                                              .withValues(alpha: 0.12),
                                          borderRadius: BorderRadius.circular(20),
                                        ),
                                        child: Text(
                                          _statusLabel(l10n, item.status),
                                          style: TextStyle(
                                            color: _statusColor(context, item.status),
                                            fontSize: 12,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    item.sessionDate.toIso8601String().split('T').first,
                                    style: theme.textTheme.bodySmall,
                                  ),
                                  if (item.studentName != null) ...[
                                    const SizedBox(height: 4),
                                    Text(
                                      '${l10n.identityStudentLabel}: ${item.studentName}',
                                      style: theme.textTheme.bodySmall,
                                    ),
                                  ],
                                  const SizedBox(height: 8),
                                  Text(item.reason),
                                  if (item.reviewNote != null) ...[
                                    const SizedBox(height: 8),
                                    Text(
                                      '${l10n.excuseReviewNote}: ${item.reviewNote}',
                                      style: theme.textTheme.bodySmall,
                                    ),
                                  ],
                                  const SizedBox(height: 8),
                                  Wrap(
                                    spacing: 8,
                                    children: [
                                      if (item.attachment != null)
                                        TextButton.icon(
                                          onPressed: () => _openAttachment(item.attachment!),
                                          icon: const Icon(Icons.attachment_outlined),
                                          label: Text(item.attachment!.name),
                                        ),
                                      if (!widget.reviewMode && item.isPending)
                                        TextButton.icon(
                                          onPressed: () => _withdraw(item),
                                          icon: const Icon(Icons.undo),
                                          label: Text(l10n.excuseWithdraw),
                                        ),
                                      if (widget.reviewMode && item.isPending) ...[
                                        FilledButton.tonalIcon(
                                          onPressed: () => _review(item, approve: true),
                                          icon: const Icon(Icons.check),
                                          label: Text(l10n.excuseApprove),
                                        ),
                                        OutlinedButton.icon(
                                          onPressed: () => _review(item, approve: false),
                                          icon: const Icon(Icons.close),
                                          label: Text(l10n.excuseReject),
                                        ),
                                      ],
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}

/// نموذج رفع عذر: اختيار المحاضرة، السبب، ومرفق صورة/PDF.
class NewExcusePage extends StatefulWidget {
  const NewExcusePage({super.key, required this.api, required this.session});

  final ExcusesApi api;
  final SessionController session;

  @override
  State<NewExcusePage> createState() => _NewExcusePageState();
}

class _NewExcusePageState extends State<NewExcusePage> {
  final _formKey = GlobalKey<FormState>();
  final _reason = TextEditingController();
  final _picker = ImagePicker();
  bool _loading = true;
  bool _submitting = false;
  String? _error;
  List<ExcuseSession> _sessions = const [];
  String? _sessionId;
  XFile? _file;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _reason.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final sessions = await widget.api.eligibleSessions();
      if (!mounted) {
        return;
      }
      setState(() {
        _sessions = sessions;
        _sessionId = sessions.isEmpty ? null : sessions.first.sessionId;
        _loading = false;
      });
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _error = error.messageAr ?? AppLocalizations.of(context)!.unexpectedError;
        _loading = false;
      });
    }
  }

  Future<void> _pick(ImageSource source) async {
    try {
      final file = await _picker.pickImage(source: source, imageQuality: 70);
      if (file != null && mounted) {
        setState(() => _file = file);
      }
    } catch (_) {
      // رفض إذن الكاميرا/المعرض لا يُسقط الشاشة
    }
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context)!;
    if (!(_formKey.currentState?.validate() ?? false) || _sessionId == null) {
      return;
    }
    setState(() => _submitting = true);
    try {
      await widget.api.submit(
        sessionId: _sessionId!,
        reason: _reason.text.trim(),
        filePath: _file?.path,
        fileName: _file?.name,
      );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.excuseSubmitted)),
      );
      Navigator.of(context).pop(true);
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _error = error.messageAr ?? l10n.unexpectedError);
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.excuseNewTitle)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Form(
              key: _formKey,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (_sessions.isEmpty)
                    Card(
                      child: ListTile(
                        leading: const Icon(Icons.info_outline),
                        title: Text(l10n.excuseNoSessions),
                      ),
                    )
                  else
                    DropdownButtonFormField<String>(
                      key: const Key('excuseSessionField'),
                      initialValue: _sessionId,
                      decoration: InputDecoration(
                        labelText: l10n.excuseSelectSession,
                        border: const OutlineInputBorder(),
                      ),
                      items: _sessions
                          .map(
                            (session) => DropdownMenuItem(
                              value: session.sessionId,
                              child: Text(
                                '${session.courseName} — '
                                '${session.date.toIso8601String().split('T').first}',
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          )
                          .toList(),
                      onChanged: (value) => setState(() => _sessionId = value),
                    ),
                  const SizedBox(height: 12),
                  TextFormField(
                    key: const Key('excuseReasonField'),
                    controller: _reason,
                    maxLines: 4,
                    decoration: InputDecoration(
                      labelText: l10n.excuseReasonLabel,
                      hintText: l10n.excuseReasonHint,
                      border: const OutlineInputBorder(),
                    ),
                    validator: (value) => (value == null || value.trim().length < 5)
                        ? l10n.fieldRequired
                        : null,
                  ),
                  const SizedBox(height: 12),
                  Card(
                    child: Column(
                      children: [
                        ListTile(
                          leading: const Icon(Icons.attach_file),
                          title: Text(
                            _file == null ? l10n.excuseAttach : l10n.excuseAttachmentChosen,
                          ),
                          subtitle: _file == null ? null : Text(_file!.name),
                        ),
                        Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Wrap(
                            spacing: 8,
                            children: [
                              OutlinedButton.icon(
                                onPressed: () => _pick(ImageSource.camera),
                                icon: const Icon(Icons.photo_camera_outlined),
                                label: Text(l10n.excuseAttachCamera),
                              ),
                              OutlinedButton.icon(
                                onPressed: () => _pick(ImageSource.gallery),
                                icon: const Icon(Icons.photo_library_outlined),
                                label: Text(l10n.excuseAttachGallery),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 12),
                    Text(
                      _error!,
                      style: TextStyle(color: Theme.of(context).colorScheme.error),
                    ),
                  ],
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    key: const Key('submitExcuseButton'),
                    onPressed: _submitting || _sessions.isEmpty ? null : _submit,
                    icon: const Icon(Icons.send),
                    label: Text(l10n.excuseSubmit),
                  ),
                ],
              ),
            ),
    );
  }
}
