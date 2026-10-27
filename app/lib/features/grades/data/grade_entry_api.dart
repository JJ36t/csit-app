import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

/// تقييم داخل مادة (كوز/مختبر/نصفي/نهائي) كما يعيده `GET /offerings/{id}/grades`.
class GradeAssessment {
  const GradeAssessment({
    required this.id,
    required this.name,
    required this.kind,
    required this.maxScore,
    required this.weight,
    required this.isPublished,
  });

  final String id;
  final String name;
  final String kind;
  final double maxScore;
  final double weight;
  final bool isPublished;

  factory GradeAssessment.fromJson(Map<String, dynamic> json) => GradeAssessment(
        id: json['assessment_id'] as String,
        name: json['name'] as String? ?? '',
        kind: json['kind'] as String? ?? 'other',
        maxScore: (json['max_score'] as num?)?.toDouble() ?? 100,
        weight: (json['weight'] as num?)?.toDouble() ?? 0,
        isPublished: json['is_published'] as bool? ?? false,
      );
}

class GradeStudentRow {
  const GradeStudentRow({
    required this.studentId,
    required this.universityId,
    required this.fullName,
    required this.scores,
    required this.weightedTotal,
    required this.weightSum,
  });

  final String studentId;
  final String universityId;
  final String fullName;

  /// معرّف التقييم → الدرجة.
  final Map<String, double> scores;
  final double weightedTotal;
  final double weightSum;

  factory GradeStudentRow.fromJson(Map<String, dynamic> json) => GradeStudentRow(
        studentId: json['student_id'] as String,
        universityId: json['university_id'] as String? ?? '',
        fullName: json['full_name_ar'] as String? ?? '',
        scores: (json['scores'] as Map?)?.map(
              (key, value) => MapEntry(key.toString(), (value as num).toDouble()),
            ) ??
            const {},
        weightedTotal: (json['weighted_total'] as num?)?.toDouble() ?? 0,
        weightSum: (json['weight_sum'] as num?)?.toDouble() ?? 0,
      );
}

class OfferingGrades {
  const OfferingGrades({
    required this.offeringId,
    required this.courseCode,
    required this.courseName,
    required this.assessments,
    required this.students,
  });

  final String offeringId;
  final String courseCode;
  final String courseName;
  final List<GradeAssessment> assessments;
  final List<GradeStudentRow> students;

  factory OfferingGrades.fromJson(Map<String, dynamic> json) => OfferingGrades(
        offeringId: json['offering_id'] as String,
        courseCode: json['course_code'] as String? ?? '',
        courseName: json['course_name_ar'] as String? ?? '',
        assessments: (json['assessments'] as List<dynamic>? ?? [])
            .whereType<Map<String, dynamic>>()
            .map(GradeAssessment.fromJson)
            .toList(),
        students: (json['students'] as List<dynamic>? ?? [])
            .whereType<Map<String, dynamic>>()
            .map(GradeStudentRow.fromJson)
            .toList(),
      );
}

/// واجهة إدخال الدرجات للتدريسي (الشاشة 8 في نموذج التصميم).
abstract class GradeEntryApi {
  Future<OfferingGrades> load(String offeringId);

  Future<GradeAssessment> createAssessment({
    required String offeringId,
    required String name,
    required String kind,
    required double maxScore,
    required double weight,
  });

  /// حفظ مسودة: خريطة معرّف الطالب → الدرجة.
  Future<void> saveScores(String assessmentId, Map<String, double> scores);

  /// النشر بموافقة الكلية (مدير الكلية فقط على الخادم).
  Future<int> publish(String assessmentId);
}

class HttpGradeEntryApi implements GradeEntryApi {
  HttpGradeEntryApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final AuthedDio _authed;

  Options _auth(String token) =>
      Options(headers: {'Authorization': 'Bearer $token'});

  @override
  Future<OfferingGrades> load(String offeringId) async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/offerings/$offeringId/grades',
          options: _auth(token),
        ),
      );
      return OfferingGrades.fromJson(response.data ?? const <String, dynamic>{});
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<GradeAssessment> createAssessment({
    required String offeringId,
    required String name,
    required String kind,
    required double maxScore,
    required double weight,
  }) async {
    try {
      final response = await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/assessments',
          data: {
            'offering_id': offeringId,
            'name': name,
            'kind': kind,
            'max_score': maxScore,
            'weight': weight,
          },
          options: _auth(token),
        ),
      );
      return GradeAssessment.fromJson(response.data ?? const <String, dynamic>{});
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<void> saveScores(String assessmentId, Map<String, double> scores) async {
    try {
      await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/assessments/$assessmentId/grades',
          data: {
            'rows': scores.entries
                .map((entry) => {'student_id': entry.key, 'score': entry.value})
                .toList(),
          },
          options: _auth(token),
        ),
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<int> publish(String assessmentId) async {
    try {
      final response = await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/assessments/$assessmentId/publish',
          options: _auth(token),
        ),
      );
      return response.data?['notified'] as int? ?? 0;
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }
}
