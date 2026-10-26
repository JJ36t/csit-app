import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/grades_api.dart';

/// درجات الطالب (نموذج الشاشة 7): لكل مادة تقييماتها المنشورة والمجموع الموزون.
class GradesPage extends StatefulWidget {
  const GradesPage({super.key, required this.api, required this.session});

  final GradesApi api;
  final SessionController session;

  @override
  State<GradesPage> createState() => _GradesPageState();
}

class _GradesPageState extends State<GradesPage> {
  bool _loading = true;
  String? _error;
  List<GradeCourse> _courses = const [];

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
      final courses = await widget.api.myGrades();
      if (!mounted) {
        return;
      }
      setState(() {
        _courses = courses;
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
      appBar: AppBar(title: Text(l10n.gradesTitle)),
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
                          key: const Key('gradesRetry'),
                          onPressed: _load,
                          icon: const Icon(Icons.refresh),
                          label: Text(l10n.retryButton),
                        ),
                      ],
                    ),
                  )
                : _courses.isEmpty
                    ? Center(child: Text(l10n.noOfferings))
                    : ListView.separated(
                        padding: const EdgeInsets.all(12),
                        itemCount: _courses.length,
                        separatorBuilder: (context, index) =>
                            const SizedBox(height: 10),
                        itemBuilder: (context, index) =>
                            _CourseCard(course: _courses[index]),
                      ),
      ),
    );
  }
}

class _CourseCard extends StatelessWidget {
  const _CourseCard({required this.course});

  final GradeCourse course;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(course.courseNameAr,
                          style: theme.textTheme.titleSmall),
                      Text(course.courseCode,
                          style: theme.textTheme.bodySmall),
                    ],
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    l10n.weightedOfTotal(
                      _fmt(course.weightedTotal),
                      _fmt(course.weightSum),
                    ),
                    key: Key('weightedTotal-${course.offeringId}'),
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: theme.colorScheme.onPrimaryContainer,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (course.assessments.isEmpty)
              Text(l10n.gradesEmpty, style: theme.textTheme.bodySmall)
            else
              ...course.assessments.map(
                (assessment) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          '${assessment.name} · ${l10n.weightShort(_fmt(assessment.weight))}',
                          style: theme.textTheme.bodySmall,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Text(
                        assessment.score == null
                            ? l10n.notGradedYet
                            : l10n.scoreOfMax(
                                _fmt(assessment.score!),
                                _fmt(assessment.maxScore),
                              ),
                        style: theme.textTheme.bodySmall?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: assessment.score == null
                              ? theme.colorScheme.outline
                              : theme.colorScheme.onSurface,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  String _fmt(double value) {
    if (value == value.roundToDouble()) {
      return value.toStringAsFixed(0);
    }
    return value.toStringAsFixed(1);
  }
}
