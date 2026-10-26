import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

/// تقييم منشور داخل مادة، بدرجة الطالب إن رُصدت.
class GradeAssessment {
  const GradeAssessment({
    required this.assessmentId,
    required this.name,
    required this.kind,
    required this.maxScore,
    required this.weight,
    this.score,
  });

  final String assessmentId;
  final String name;

  /// quiz / lab / midterm / final / other.
  final String kind;
  final double maxScore;
  final double weight;
  final double? score;

  factory GradeAssessment.fromJson(Map<String, dynamic> json) => GradeAssessment(
        assessmentId: json['assessment_id'] as String,
        name: json['name'] as String? ?? '',
        kind: json['kind'] as String? ?? 'other',
        maxScore: (json['max_score'] as num?)?.toDouble() ?? 0,
        weight: (json['weight'] as num?)?.toDouble() ?? 0,
        score: (json['score'] as num?)?.toDouble(),
      );
}

/// درجات مادة واحدة كما يراها الطالب (المنشور فقط).
class GradeCourse {
  const GradeCourse({
    required this.offeringId,
    required this.courseCode,
    required this.courseNameAr,
    required this.assessments,
    required this.weightedTotal,
    required this.weightSum,
  });

  final String offeringId;
  final String courseCode;
  final String courseNameAr;
  final List<GradeAssessment> assessments;
  final double weightedTotal;
  final double weightSum;

  factory GradeCourse.fromJson(Map<String, dynamic> json) => GradeCourse(
        offeringId: json['offering_id'] as String,
        courseCode: json['course_code'] as String? ?? '',
        courseNameAr: json['course_name_ar'] as String? ?? '',
        assessments: (json['assessments'] as List<dynamic>? ?? [])
            .whereType<Map<String, dynamic>>()
            .map(GradeAssessment.fromJson)
            .toList(),
        weightedTotal: (json['weighted_total'] as num?)?.toDouble() ?? 0,
        weightSum: (json['weight_sum'] as num?)?.toDouble() ?? 0,
      );
}

/// واجهة الدرجات — تُختبر ببديل في الذاكرة.
abstract class GradesApi {
  Future<List<GradeCourse>> myGrades();
}

class HttpGradesApi implements GradesApi {
  HttpGradesApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final AuthedDio _authed;

  @override
  Future<List<GradeCourse>> myGrades() async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/grades',
          options: Options(headers: {'Authorization': 'Bearer $token'}),
        ),
      );
      return (response.data?['items'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(GradeCourse.fromJson)
          .toList();
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }
}
