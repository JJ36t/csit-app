import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

/// مادة (offering) يراها المستخدم — أساس شاشتي المواد والدرجات.
class OfferingSummary {
  const OfferingSummary({
    required this.offeringId,
    required this.courseCode,
    required this.courseNameAr,
    required this.kind,
    required this.stage,
    required this.groupName,
    required this.studyType,
    this.instructorNameAr,
  });

  final String offeringId;
  final String courseCode;
  final String courseNameAr;

  /// theory / lab.
  final String kind;
  final int stage;
  final String groupName;

  /// morning / evening.
  final String studyType;
  final String? instructorNameAr;

  factory OfferingSummary.fromJson(Map<String, dynamic> json) => OfferingSummary(
        offeringId: json['offering_id'] as String,
        courseCode: json['course_code'] as String? ?? '',
        courseNameAr: json['course_name_ar'] as String? ?? '',
        kind: json['kind'] as String? ?? 'theory',
        stage: json['stage'] as int? ?? 1,
        groupName: json['group_name'] as String? ?? '',
        studyType: json['study_type'] as String? ?? 'morning',
        instructorNameAr: json['instructor_name_ar'] as String?,
      );
}

/// مادة دراسية (ملف PDF أو رابط فيديو/رابط).
class MaterialItem {
  const MaterialItem({
    required this.materialId,
    required this.title,
    required this.kind,
    this.weekNo,
    required this.isPublished,
    this.url,
    this.downloadUrl,
    this.fileName,
    this.fileSize,
  });

  final String materialId;
  final String title;

  /// pdf / video_link / link.
  final String kind;
  final int? weekNo;
  final bool isPublished;
  final String? url;
  final String? downloadUrl;
  final String? fileName;
  final int? fileSize;

  factory MaterialItem.fromJson(Map<String, dynamic> json) => MaterialItem(
        materialId: json['material_id'] as String,
        title: json['title'] as String? ?? '',
        kind: json['kind'] as String? ?? 'pdf',
        weekNo: json['week_no'] as int?,
        isPublished: json['is_published'] as bool? ?? false,
        url: json['url'] as String?,
        downloadUrl: json['download_url'] as String?,
        fileName: json['file_name'] as String?,
        fileSize: json['file_size'] as int?,
      );
}

/// واجهة المواد — تُختبر ببديل في الذاكرة.
abstract class MaterialsApi {
  Future<List<OfferingSummary>> myOfferings();

  Future<List<MaterialItem>> materials(String offeringId);
}

class HttpMaterialsApi implements MaterialsApi {
  HttpMaterialsApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final AuthedDio _authed;

  Options _auth(String token) =>
      Options(headers: {'Authorization': 'Bearer $token'});

  @override
  Future<List<OfferingSummary>> myOfferings() async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/offerings',
          options: _auth(token),
        ),
      );
      return (response.data?['items'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(OfferingSummary.fromJson)
          .toList();
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<List<MaterialItem>> materials(String offeringId) async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/offerings/$offeringId/materials',
          options: _auth(token),
        ),
      );
      return (response.data?['items'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(MaterialItem.fromJson)
          .toList();
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }
}
