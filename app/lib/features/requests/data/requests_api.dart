import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/authed_dio.dart';
import '../../../core/storage/token_store.dart';

/// طلب موجز في القائمة.
class RequestSummary {
  const RequestSummary({
    required this.id,
    required this.category,
    required this.categoryLabel,
    required this.subject,
    required this.status,
    this.updatedAt,
    this.assignedTo,
  });

  final String id;
  final String category;
  final String categoryLabel;
  final String subject;

  /// open | in_progress | resolved | closed
  final String status;
  final DateTime? updatedAt;
  final String? assignedTo;

  bool get isClosed => status == 'resolved' || status == 'closed';

  factory RequestSummary.fromJson(Map<String, dynamic> json) => RequestSummary(
        id: json['request_id'] as String,
        category: json['category'] as String? ?? 'other',
        categoryLabel: json['category_label'] as String? ?? '',
        subject: json['subject'] as String? ?? '',
        status: json['status'] as String? ?? 'open',
        updatedAt: DateTime.tryParse(json['updated_at'] as String? ?? ''),
        assignedTo: json['assigned_to'] as String?,
      );
}

class RequestMessageItem {
  const RequestMessageItem({
    required this.id,
    required this.senderId,
    required this.body,
    this.createdAt,
  });

  final String id;
  final String senderId;
  final String body;
  final DateTime? createdAt;

  factory RequestMessageItem.fromJson(Map<String, dynamic> json) => RequestMessageItem(
        id: json['message_id'] as String,
        senderId: json['sender_id'] as String? ?? '',
        body: json['body'] as String? ?? '',
        createdAt: DateTime.tryParse(json['created_at'] as String? ?? ''),
      );
}

class RequestDetail {
  const RequestDetail({required this.summary, required this.messages});

  final RequestSummary summary;
  final List<RequestMessageItem> messages;

  factory RequestDetail.fromJson(Map<String, dynamic> json) => RequestDetail(
        summary: RequestSummary.fromJson(json),
        messages: (json['messages'] as List<dynamic>? ?? [])
            .whereType<Map<String, dynamic>>()
            .map(RequestMessageItem.fromJson)
            .toList(),
      );
}

abstract class RequestsApi {
  Future<List<RequestSummary>> list();

  Future<RequestDetail> detail(String requestId);

  Future<RequestDetail> create({
    required String category,
    required String subject,
    required String body,
  });

  Future<RequestDetail> sendMessage(String requestId, String body);

  /// لرئيس القسم/الإدارة: تغيير الحالة أو الإسناد.
  Future<void> updateRequest(
    String requestId, {
    String? status,
    String? assignedTo,
  });
}

class HttpRequestsApi implements RequestsApi {
  HttpRequestsApi({required Dio dio, required TokenStore store})
      : _dio = dio,
        _authed = AuthedDio(dio: dio, store: store);

  final Dio _dio;
  final AuthedDio _authed;

  Options _auth(String token) =>
      Options(headers: {'Authorization': 'Bearer $token'});

  @override
  Future<List<RequestSummary>> list() async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/requests',
          options: _auth(token),
        ),
      );
      return (response.data?['items'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(RequestSummary.fromJson)
          .toList();
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<RequestDetail> detail(String requestId) async {
    try {
      final response = await _authed.send(
        (token) => _dio.get<Map<String, dynamic>>(
          '/api/v1/requests/$requestId',
          options: _auth(token),
        ),
      );
      return RequestDetail.fromJson(response.data ?? const <String, dynamic>{});
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<RequestDetail> create({
    required String category,
    required String subject,
    required String body,
  }) async {
    try {
      final response = await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/requests',
          data: {'category': category, 'subject': subject, 'body': body},
          options: _auth(token),
        ),
      );
      return RequestDetail.fromJson(response.data ?? const <String, dynamic>{});
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<RequestDetail> sendMessage(String requestId, String body) async {
    try {
      final response = await _authed.send(
        (token) => _dio.post<Map<String, dynamic>>(
          '/api/v1/requests/$requestId/messages',
          data: {'body': body},
          options: _auth(token),
        ),
      );
      return RequestDetail.fromJson(response.data ?? const <String, dynamic>{});
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  @override
  Future<void> updateRequest(
    String requestId, {
    String? status,
    String? assignedTo,
  }) async {
    try {
      await _authed.send(
        (token) => _dio.patch<Map<String, dynamic>>(
          '/api/v1/admin/requests/$requestId',
          data: {
            if (status != null) 'status': status,
            if (assignedTo != null) 'assigned_to': assignedTo,
          },
          options: _auth(token),
        ),
      );
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }
}
