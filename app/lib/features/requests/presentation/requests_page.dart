import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/requests_api.dart';

/// قائمة الطلبات: الطالب يرى طلباته ويفتح طلباً جديداً، والموظف يرى طلبات قسمه.
class RequestsPage extends StatefulWidget {
  const RequestsPage({super.key, required this.api, required this.session});

  final RequestsApi api;
  final SessionController session;

  @override
  State<RequestsPage> createState() => _RequestsPageState();
}

class _RequestsPageState extends State<RequestsPage> {
  bool _loading = true;
  String? _error;
  List<RequestSummary> _items = const [];

  bool get _isStudent => widget.session.profile?.isStudent ?? false;

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
      final items = await widget.api.list();
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

  Future<void> _open(RequestSummary item) async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => RequestThreadPage(
          api: widget.api,
          session: widget.session,
          requestId: item.id,
        ),
      ),
    );
    await _load();
  }

  Future<void> _create() async {
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: _NewRequestForm(api: widget.api),
      ),
    );
    if (created == true) {
      await _load();
    }
  }

  String _statusLabel(AppLocalizations l10n, String status) => switch (status) {
        'in_progress' => l10n.requestStatusInProgress,
        'resolved' => l10n.requestStatusResolved,
        'closed' => l10n.requestStatusClosed,
        _ => l10n.requestStatusOpen,
      };

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.requestsTitle)),
      floatingActionButton: _isStudent
          ? FloatingActionButton.extended(
              key: const Key('newRequestButton'),
              onPressed: _create,
              icon: const Icon(Icons.add_comment_outlined),
              label: Text(l10n.requestNewTitle),
            )
          : null,
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
                          Icon(Icons.forum_outlined,
                              size: 56, color: theme.colorScheme.outline),
                          const SizedBox(height: 12),
                          Text(l10n.requestsEmpty, textAlign: TextAlign.center),
                        ],
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(12, 12, 12, 96),
                        itemCount: _items.length,
                        itemBuilder: (context, index) {
                          final item = _items[index];
                          return Card(
                            child: ListTile(
                              key: Key('request-${item.id}'),
                              leading: const Icon(Icons.chat_bubble_outline),
                              title: Text(item.subject),
                              subtitle: Text(
                                '${item.categoryLabel} · '
                                '${item.updatedAt == null ? '' : formatHm(item.updatedAt!)}',
                              ),
                              trailing: Chip(
                                label: Text(
                                  _statusLabel(l10n, item.status),
                                  style: const TextStyle(fontSize: 11),
                                ),
                                visualDensity: VisualDensity.compact,
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

class _NewRequestForm extends StatefulWidget {
  const _NewRequestForm({required this.api});

  final RequestsApi api;

  @override
  State<_NewRequestForm> createState() => _NewRequestFormState();
}

class _NewRequestFormState extends State<_NewRequestForm> {
  final _formKey = GlobalKey<FormState>();
  final _subject = TextEditingController();
  final _body = TextEditingController();
  String _category = 'academic';
  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _subject.dispose();
    _body.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context)!;
    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }
    setState(() => _submitting = true);
    try {
      await widget.api.create(
        category: _category,
        subject: _subject.text.trim(),
        body: _body.text.trim(),
      );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.requestCreated)),
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
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.requestNewTitle, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _category,
              decoration: InputDecoration(
                labelText: l10n.requestCategoryLabel,
                border: const OutlineInputBorder(),
              ),
              items: [
                DropdownMenuItem(value: 'academic', child: Text(l10n.requestCategoryAcademic)),
                DropdownMenuItem(value: 'schedule', child: Text(l10n.requestCategorySchedule)),
                DropdownMenuItem(value: 'grades', child: Text(l10n.requestCategoryGrades)),
                DropdownMenuItem(value: 'documents', child: Text(l10n.requestCategoryDocuments)),
                DropdownMenuItem(value: 'other', child: Text(l10n.requestCategoryOther)),
              ],
              onChanged: (value) => setState(() => _category = value ?? 'academic'),
            ),
            const SizedBox(height: 12),
            TextFormField(
              key: const Key('requestSubjectField'),
              controller: _subject,
              decoration: InputDecoration(
                labelText: l10n.requestSubjectLabel,
                border: const OutlineInputBorder(),
              ),
              validator: (value) =>
                  (value == null || value.trim().length < 3) ? l10n.fieldRequired : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              key: const Key('requestBodyField'),
              controller: _body,
              maxLines: 4,
              decoration: InputDecoration(
                labelText: l10n.requestBodyLabel,
                border: const OutlineInputBorder(),
              ),
              validator: (value) =>
                  (value == null || value.trim().length < 5) ? l10n.fieldRequired : null,
            ),
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            const SizedBox(height: 16),
            FilledButton.icon(
              key: const Key('submitRequestButton'),
              onPressed: _submitting ? null : _submit,
              icon: const Icon(Icons.send),
              label: Text(l10n.requestSend),
            ),
          ],
        ),
      ),
    );
  }
}

/// محادثة الطلب: فقاعات الرسائل + صندوق رد، وتغيير الحالة للموظف.
class RequestThreadPage extends StatefulWidget {
  const RequestThreadPage({
    super.key,
    required this.api,
    required this.session,
    required this.requestId,
  });

  final RequestsApi api;
  final SessionController session;
  final String requestId;

  @override
  State<RequestThreadPage> createState() => _RequestThreadPageState();
}

class _RequestThreadPageState extends State<RequestThreadPage> {
  final _reply = TextEditingController();
  bool _loading = true;
  bool _sending = false;
  String? _error;
  RequestDetail? _detail;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _reply.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final detail = await widget.api.detail(widget.requestId);
      if (!mounted) {
        return;
      }
      setState(() {
        _detail = detail;
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

  Future<void> _send() async {
    final text = _reply.text.trim();
    if (text.isEmpty) {
      return;
    }
    final l10n = AppLocalizations.of(context)!;
    setState(() => _sending = true);
    try {
      final detail = await widget.api.sendMessage(widget.requestId, text);
      if (!mounted) {
        return;
      }
      _reply.clear();
      setState(() => _detail = detail);
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    } finally {
      if (mounted) {
        setState(() => _sending = false);
      }
    }
  }

  Future<void> _changeStatus(String status) async {
    try {
      await widget.api.updateRequest(widget.requestId, status: status);
      await _load();
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.messageAr ?? AppLocalizations.of(context)!.unexpectedError)),
      );
    }
  }

  String _statusLabel(AppLocalizations l10n, String status) => switch (status) {
        'in_progress' => l10n.requestStatusInProgress,
        'resolved' => l10n.requestStatusResolved,
        'closed' => l10n.requestStatusClosed,
        _ => l10n.requestStatusOpen,
      };

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final detail = _detail;
    final myId = widget.session.profile?.id ?? '';
    final isStaff = !(widget.session.profile?.isStudent ?? true);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.requestDetailTitle),
        actions: [
          if (detail != null && isStaff)
            PopupMenuButton<String>(
              key: const Key('requestStatusMenu'),
              icon: const Icon(Icons.more_vert),
              onSelected: _changeStatus,
              itemBuilder: (context) => [
                PopupMenuItem(value: 'in_progress', child: Text(l10n.requestStatusInProgress)),
                PopupMenuItem(value: 'resolved', child: Text(l10n.requestStatusResolved)),
                PopupMenuItem(value: 'closed', child: Text(l10n.requestStatusClosed)),
              ],
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(detail!.summary.subject,
                                    style: theme.textTheme.titleMedium),
                                Text(
                                  '${detail.summary.categoryLabel} · '
                                  '${_statusLabel(l10n, detail.summary.status)}',
                                  style: theme.textTheme.bodySmall,
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Divider(height: 1),
                    Expanded(
                      child: detail.messages.isEmpty
                          ? Center(child: Text(l10n.conversationEmpty))
                          : ListView.builder(
                              padding: const EdgeInsets.all(12),
                              itemCount: detail.messages.length,
                              itemBuilder: (context, index) {
                                final message = detail.messages[index];
                                final mine = message.senderId == myId;
                                return Align(
                                  alignment: mine
                                      ? AlignmentDirectional.centerEnd
                                      : AlignmentDirectional.centerStart,
                                  child: Container(
                                    constraints: BoxConstraints(
                                      maxWidth: MediaQuery.of(context).size.width * 0.78,
                                    ),
                                    margin: const EdgeInsets.symmetric(vertical: 4),
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: mine
                                          ? theme.colorScheme.primaryContainer
                                          : theme.colorScheme.surfaceContainerHighest,
                                      borderRadius: BorderRadius.circular(14),
                                    ),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(message.body),
                                        if (message.createdAt != null) ...[
                                          const SizedBox(height: 4),
                                          Text(
                                            formatHm(message.createdAt!),
                                            style: theme.textTheme.bodySmall,
                                          ),
                                        ],
                                      ],
                                    ),
                                  ),
                                );
                              },
                            ),
                    ),
                    SafeArea(
                      top: false,
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
                        child: detail.summary.isClosed
                            ? Text(
                                l10n.requestClosedNotice,
                                style: theme.textTheme.bodySmall,
                              )
                            : Row(
                                children: [
                                  Expanded(
                                    child: TextField(
                                      key: const Key('replyField'),
                                      controller: _reply,
                                      minLines: 1,
                                      maxLines: 4,
                                      decoration: InputDecoration(
                                        hintText: l10n.requestReplyHint,
                                        border: const OutlineInputBorder(),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  IconButton.filled(
                                    key: const Key('sendReplyButton'),
                                    onPressed: _sending ? null : _send,
                                    icon: const Icon(Icons.send),
                                    tooltip: l10n.requestSendReply,
                                  ),
                                ],
                              ),
                      ),
                    ),
                  ],
                ),
    );
  }
}
