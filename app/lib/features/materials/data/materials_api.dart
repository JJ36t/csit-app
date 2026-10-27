import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

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

  Map<String, dynamic> toJson() => {
        'material_id': materialId,
        'title': title,
        'kind': kind,
        'week_no': weekNo,
        'is_published': isPublished,
        'url': url,
        'download_url': downloadUrl,
        'file_name': fileName,
        'file_size': fileSize,
      };
}

/// نتيجة تحميل مواد مقرر مع مؤشر الذاكرة المحلية.
class MaterialsData {
  const MaterialsData({
    required this.items,
    this.fetchedAt,
    this.fromCache = false,
  });

  final List<MaterialItem> items;
  final DateTime? fetchedAt;
  final bool fromCache;
}

/// تخزين محلي لمواد كل مقرر — يفتح الشاشة بلا إنترنت.
abstract class MaterialsCache {
  Future<void> save(String offeringId, List<MaterialItem> items, DateTime at);

  Future<({List<MaterialItem> items, DateTime at})?> read(String offeringId);
}

class PrefsMaterialsCache implements MaterialsCache {
  static const _prefix = 'csit.materials.cache.v1.';

  @override
  Future<void> save(String offeringId, List<MaterialItem> items, DateTime at) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      '$_prefix$offeringId',
      jsonEncode({
        'saved_at': at.toUtc().toIso8601String(),
        'items': items.map((item) => item.toJson()).toList(),
      }),
    );
  }

  @override
  Future<({List<MaterialItem> items, DateTime at})?> read(String offeringId) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('$_prefix$offeringId');
    if (raw == null) {
      return null;
    }
    try {
      final body = jsonDecode(raw) as Map<String, dynamic>;
      final items = (body['items'] as List<dynamic>)
          .whereType<Map<String, dynamic>>()
          .map(MaterialItem.fromJson)
          .toList();
      return (items: items, at: DateTime.parse(body['saved_at'] as String));
    } catch (_) {
      return null;
    }
  }
}

/// واجهة المواد — تُختبر ببديل في الذاكرة.
abstract class MaterialsApi {
  Future<List<OfferingSummary>> myOfferings();

  Future<MaterialsData> materials(String offeringId);
}

class HttpMaterialsApi implements MaterialsApi {
  HttpMaterialsApi({
    required Dio dio,
    required TokenStore store,
    MaterialsCache? cache,
  })  : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store),
        _cache = cache ?? PrefsMaterialsCache();

  final Dio _dio;
  final AuthedDio _authed;
  final MaterialsCache _cache;

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
  Future<MaterialsData> materials(String offeringId) async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/offerings/$offeringId/materials',
          options: _auth(token),
        ),
      );
      final items = (response.data?['items'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(MaterialItem.fromJson)
          .toList();
      final now = DateTime.now().toUtc();
      await _cache.save(offeringId, items, now);
      return MaterialsData(items: items, fetchedAt: now);
    } on ApiException catch (error) {
      if (error.statusCode == 401 || error.statusCode == 403) {
        rethrow;
      }
      final cached = await _cache.read(offeringId);
      if (cached == null) {
        rethrow;
      }
      return MaterialsData(
        items: cached.items,
        fetchedAt: cached.at,
        fromCache: true,
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }
}
