import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/network/api_client.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../../materials/data/materials_api.dart';
import '../data/grade_entry_api.dart';

/// الشاشة 8 في نموذج التصميم: إدخال درجات تقييم لشعبة، كمسودة أولاً.
///
/// قواعد الخطة: التدريسي يدخل المسودة، والنشر بموافقة مدير الكلية — لذلك
/// يظهر زر النشر معطّلاً لغير المدير مع سبب واضح، ولا يُسمح بتعديل تقييم منشور.
class GradeEntryPage extends StatefulWidget {
  const GradeEntryPage({
    super.key,
    required this.api,
    required this.offeringsApi,
    required this.session,
  });

  final GradeEntryApi api;
  final MaterialsApi offeringsApi;
  final SessionController session;

  @override
  State<GradeEntryPage> createState() => _GradeEntryPageState();
}

class _GradeEntryPageState extends State<GradeEntryPage> {
  final Map<String, TextEditingController> _controllers = {};
  List<OfferingSummary> _offerings = const [];
  OfferingGrades? _grades;
  String? _offeringId;
  String? _assessmentId;
  bool _loading = true;
  bool _saving = false;
  String? _error;

  bool get _isAdmin => widget.session.profile?.role == 'college_admin';

  GradeAssessment? get _assessment {
    final grades = _grades;
    if (grades == null || _assessmentId == null) {
      return null;
    }
    for (final item in grades.assessments) {
      if (item.id == _assessmentId) {
        return item;
      }
    }
    return null;
  }

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  @override
  void dispose() {
    _disposeControllers();
    super.dispose();
  }

  void _disposeControllers() {
    for (final controller in _controllers.values) {
      controller.dispose();
    }
    _controllers.clear();
  }

  Future<void> _bootstrap() async {
    try {
      final offerings = await widget.offeringsApi.myOfferings();
      if (!mounted) {
        return;
      }
      setState(() {
        _offerings = offerings;
        _offeringId = offerings.isEmpty ? null : offerings.first.offeringId;
      });
      if (_offeringId != null) {
        await _loadGrades();
      } else {
        setState(() => _loading = false);
      }
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

  Future<void> _loadGrades({bool keepAssessment = true}) async {
    final offeringId = _offeringId;
    if (offeringId == null) {
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final grades = await widget.api.load(offeringId);
      if (!mounted) {
        return;
      }
      final previous = keepAssessment ? _assessmentId : null;
      final exists = grades.assessments.any((item) => item.id == previous);
      // التقييمات المنشورة مقفلة — نفضّل التقييم الأول غير المنشور كي يبدأ التدريسي بالإدخال
      final editable = grades.assessments.where((item) => !item.isPublished);
      setState(() {
        _grades = grades;
        _assessmentId = exists
            ? previous
            : (editable.isNotEmpty
                ? editable.first.id
                : (grades.assessments.isEmpty ? null : grades.assessments.first.id));
        _loading = false;
      });
      _syncControllers();
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
    }
  }

  void _syncControllers() {
    // لا نُحرّر المتحكمات القديمة فوراً: الحقول ما زالت في الشجرة حتى إعادة البناء
    final stale = _controllers.values.toList();
    _controllers.clear();
    if (stale.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        for (final controller in stale) {
          controller.dispose();
        }
      });
    }
    final grades = _grades;
    final assessment = _assessment;
    if (grades == null || assessment == null) {
      return;
    }
    for (final row in grades.students) {
      final value = row.scores[assessment.id];
      _controllers[row.studentId] = TextEditingController(
        text: value == null ? '' : _formatScore(value),
      );
    }
  }

  String _formatScore(double value) {
    if (value == value.roundToDouble()) {
      return value.toStringAsFixed(0);
    }
    return value.toStringAsFixed(1);
  }

  double? _scoreFor(String studentId) {
    final raw = _controllers[studentId]?.text.trim() ?? '';
    if (raw.isEmpty) {
      return null;
    }
    return double.tryParse(raw);
  }

  String? _errorFor(GradeStudentRow row, GradeAssessment assessment, AppLocalizations l10n) {
    final raw = _controllers[row.studentId]?.text.trim() ?? '';
    if (raw.isEmpty) {
      return null;
    }
    final value = double.tryParse(raw);
    if (value == null) {
      return l10n.scoreRangeError(_formatScore(assessment.maxScore));
    }
    if (value < 0 || value > assessment.maxScore) {
      return l10n.scoreRangeError(_formatScore(assessment.maxScore));
    }
    return null;
  }

  int _gradedCount(GradeAssessment assessment, AppLocalizations l10n) {
    final grades = _grades;
    if (grades == null) {
      return 0;
    }
    var count = 0;
    for (final row in grades.students) {
      if (_errorFor(row, assessment, l10n) == null &&
          (_controllers[row.studentId]?.text.trim().isNotEmpty ?? false)) {
        count++;
      }
    }
    return count;
  }

  bool _hasErrors(GradeAssessment assessment, AppLocalizations l10n) {
    final grades = _grades;
    if (grades == null) {
      return false;
    }
    return grades.students.any((row) => _errorFor(row, assessment, l10n) != null);
  }

  Future<void> _saveDraft() async {
    final l10n = AppLocalizations.of(context)!;
    final assessment = _assessment;
    final grades = _grades;
    if (assessment == null || grades == null) {
      return;
    }
    if (_hasErrors(assessment, l10n)) {
      return;
    }
    final rows = <String, double>{};
    for (final row in grades.students) {
      final value = _scoreFor(row.studentId);
      if (value != null) {
        rows[row.studentId] = value;
      }
    }
    if (rows.isEmpty) {
      return;
    }
    setState(() => _saving = true);
    try {
      await widget.api.saveScores(assessment.id, rows);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.draftSaved)),
      );
      await _loadGrades();
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    } finally {
      if (mounted) {
        setState(() => _saving = false);
      }
    }
  }

  Future<void> _publish() async {
    final l10n = AppLocalizations.of(context)!;
    final assessment = _assessment;
    if (assessment == null || !_isAdmin) {
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.publishGradesButton),
        content: Text(assessment.name),
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
    setState(() => _saving = true);
    try {
      final notified = await widget.api.publish(assessment.id);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.publishedSuccess(notified))),
      );
      await _loadGrades();
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    } finally {
      if (mounted) {
        setState(() => _saving = false);
      }
    }
  }

  Future<void> _createAssessment() async {
    final l10n = AppLocalizations.of(context)!;
    final offeringId = _offeringId;
    if (offeringId == null) {
      return;
    }
    final nameController = TextEditingController();
    final maxController = TextEditingController(text: '20');
    final weightController = TextEditingController(text: '10');
    String kind = 'quiz';

    final created = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.newAssessmentButton),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                key: const Key('assessmentNameField'),
                controller: nameController,
                decoration: InputDecoration(
                  labelText: l10n.assessmentNameLabel,
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              StatefulBuilder(
                builder: (context, setDialogState) => DropdownButtonFormField<String>(
                  initialValue: kind,
                  decoration: InputDecoration(
                    labelText: l10n.assessmentKindLabel,
                    border: const OutlineInputBorder(),
                  ),
                  items: [
                    DropdownMenuItem(value: 'quiz', child: Text(l10n.kindQuiz)),
                    DropdownMenuItem(value: 'lab', child: Text(l10n.kindLab)),
                    DropdownMenuItem(value: 'midterm', child: Text(l10n.kindMidterm)),
                    DropdownMenuItem(value: 'final', child: Text(l10n.kindFinal)),
                    DropdownMenuItem(value: 'other', child: Text(l10n.kindOther)),
                  ],
                  onChanged: (value) => setDialogState(() => kind = value ?? 'quiz'),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      key: const Key('assessmentMaxField'),
                      controller: maxController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: l10n.maxScoreLabel,
                        border: const OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      key: const Key('assessmentWeightField'),
                      controller: weightController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: l10n.weightPercentLabel,
                        border: const OutlineInputBorder(),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                l10n.assessmentWeightHint,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.cancelButton),
          ),
          FilledButton(
            key: const Key('createAssessmentButton'),
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.createAssessmentButton),
          ),
        ],
      ),
    );
    if (created != true) {
      return;
    }
    final maxScore = double.tryParse(maxController.text.trim());
    final weight = double.tryParse(weightController.text.trim());
    if (nameController.text.trim().isEmpty || maxScore == null || weight == null) {
      return;
    }
    try {
      final assessment = await widget.api.createAssessment(
        offeringId: offeringId,
        name: nameController.text.trim(),
        kind: kind,
        maxScore: maxScore,
        weight: weight,
      );
      if (!mounted) {
        return;
      }
      setState(() => _assessmentId = assessment.id);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.assessmentCreated)),
      );
      await _loadGrades();
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.messageAr ?? l10n.unexpectedError)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final grades = _grades;
    final assessment = _assessment;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.gradeEntryTitle)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(_error!, textAlign: TextAlign.center),
                        const SizedBox(height: 12),
                        FilledButton(onPressed: _bootstrap, child: Text(l10n.retryButton)),
                      ],
                    ),
                  ),
                )
              : _offerings.isEmpty
                  ? Center(child: Text(l10n.noOfferings))
                  : ListView(
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
                      children: [
                        DropdownButtonFormField<String>(
                          key: const Key('gradeOfferingField'),
                          initialValue: _offeringId,
                          decoration: InputDecoration(
                            labelText: l10n.chooseOfferingLabel,
                            border: const OutlineInputBorder(),
                          ),
                          items: _offerings
                              .map(
                                (offering) => DropdownMenuItem(
                                  value: offering.offeringId,
                                  child: Text(
                                    '${offering.courseCode} — ${offering.courseNameAr}',
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              )
                              .toList(),
                          onChanged: (value) async {
                            if (value == null) {
                              return;
                            }
                            setState(() {
                              _offeringId = value;
                              _assessmentId = null;
                            });
                            await _loadGrades(keepAssessment: false);
                          },
                        ),
                        const SizedBox(height: 12),
                        if (assessment == null)
                          Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                children: [
                                  Text(l10n.noAssessmentsYet),
                                  const SizedBox(height: 12),
                                  FilledButton.icon(
                                    onPressed: _createAssessment,
                                    icon: const Icon(Icons.add),
                                    label: Text(l10n.newAssessmentButton),
                                  ),
                                ],
                              ),
                            ),
                          )
                        else ...[
                          Card(
                            child: Padding(
                              padding: const EdgeInsets.all(12),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          '${grades!.courseName} — ${assessment.name}',
                                          style: theme.textTheme.titleMedium,
                                        ),
                                      ),
                                      if (assessment.isPublished)
                                        Chip(
                                          label: Text(l10n.assessmentPublished),
                                          visualDensity: VisualDensity.compact,
                                        ),
                                    ],
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    '${l10n.maxScoreLabel}: ${_formatScore(assessment.maxScore)} · '
                                    '${l10n.weightPercentLabel}: ${_formatScore(assessment.weight)}',
                                    style: theme.textTheme.bodySmall,
                                  ),
                                  const SizedBox(height: 8),
                                  Wrap(
                                    spacing: 8,
                                    runSpacing: 4,
                                    children: [
                                      for (final item in grades.assessments)
                                        ChoiceChip(
                                          key: Key('assessmentChip-${item.id}'),
                                          label: Text(item.name),
                                          selected: item.id == assessment.id,
                                          onSelected: (_) {
                                            setState(() => _assessmentId = item.id);
                                            _syncControllers();
                                          },
                                        ),
                                      ActionChip(
                                        avatar: const Icon(Icons.add, size: 16),
                                        label: Text(l10n.newAssessmentButton),
                                        onPressed: _createAssessment,
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  l10n.gradedOfTotal(
                                    _gradedCount(assessment, l10n),
                                    grades.students.length,
                                  ),
                                  style: theme.textTheme.bodySmall,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          LinearProgressIndicator(
                            value: grades.students.isEmpty
                                ? 0
                                : _gradedCount(assessment, l10n) / grades.students.length,
                          ),
                          const SizedBox(height: 12),
                          if (assessment.isPublished)
                            Card(
                              color: theme.colorScheme.secondaryContainer,
                              child: ListTile(
                                leading: const Icon(Icons.lock_outline),
                                title: Text(l10n.assessmentLocked),
                              ),
                            ),
                          for (var index = 0; index < grades.students.length; index++)
                            _StudentGradeRow(
                              index: index + 1,
                              row: grades.students[index],
                              controller: _controllers[grades.students[index].studentId]!,
                              maxScore: _formatScore(assessment.maxScore),
                              error: assessment.isPublished
                                  ? null
                                  : _errorFor(grades.students[index], assessment, l10n),
                              enabled: !assessment.isPublished && !_saving,
                              onChanged: (_) => setState(() {}),
                            ),
                          const SizedBox(height: 16),
                          Text(l10n.gradeEntryHint, style: theme.textTheme.bodySmall),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton.icon(
                                  key: const Key('saveDraftButton'),
                                  onPressed: (_saving ||
                                          assessment.isPublished ||
                                          _hasErrors(assessment, l10n))
                                      ? null
                                      : _saveDraft,
                                  icon: const Icon(Icons.save_outlined),
                                  label: Text(l10n.saveDraftButton),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: FilledButton.icon(
                                  key: const Key('publishGradesButton'),
                                  onPressed: (_isAdmin &&
                                          !_saving &&
                                          !assessment.isPublished &&
                                          !_hasErrors(assessment, l10n))
                                      ? _publish
                                      : null,
                                  icon: const Icon(Icons.publish_outlined),
                                  label: Text(l10n.publishGradesButton),
                                ),
                              ),
                            ],
                          ),
                          if (!_isAdmin) ...[
                            const SizedBox(height: 6),
                            Text(
                              l10n.publishNeedsAdmin,
                              style: theme.textTheme.bodySmall,
                            ),
                          ],
                        ],
                      ],
                    ),
    );
  }
}

class _StudentGradeRow extends StatelessWidget {
  const _StudentGradeRow({
    required this.index,
    required this.row,
    required this.controller,
    required this.maxScore,
    required this.error,
    required this.enabled,
    required this.onChanged,
  });

  final int index;
  final GradeStudentRow row;
  final TextEditingController controller;
  final String maxScore;
  final String? error;
  final bool enabled;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                SizedBox(
                  width: 28,
                  child: Text(
                    '$index',
                    style: theme.textTheme.bodySmall,
                    textAlign: TextAlign.center,
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(row.fullName, maxLines: 1, overflow: TextOverflow.ellipsis),
                      Text(row.universityId, style: theme.textTheme.bodySmall),
                    ],
                  ),
                ),
                SizedBox(
                  width: 86,
                  child: TextField(
                    key: Key('scoreField-${row.studentId}'),
                    controller: controller,
                    enabled: enabled,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    textAlign: TextAlign.center,
                    inputFormatters: [
                      FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
                    ],
                    decoration: InputDecoration(
                      isDense: true,
                      border: const OutlineInputBorder(),
                      contentPadding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
                      errorText: error,
                    ),
                    onChanged: onChanged,
                  ),
                ),
                const SizedBox(width: 6),
                Text('/ $maxScore', style: theme.textTheme.bodySmall),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
