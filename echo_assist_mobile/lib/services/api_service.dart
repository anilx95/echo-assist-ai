import 'package:dio/dio.dart';

import '../core/constants/api_constants.dart';
import 'storage_service.dart';
import 'token_manager.dart';

class ApiException implements Exception {
  ApiException(this.message, this.statusCode);

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class ApiService {
  ApiService._()
      : _dio = Dio(
          BaseOptions(
            baseUrl: ApiConstants.baseUrl,
            connectTimeout: const Duration(seconds: 10),
            receiveTimeout: const Duration(seconds: 20),
            headers: const {'Accept': 'application/json'},
          ),
        );

  static final ApiService instance = ApiService._();
  final Dio _dio;

  Future<Response<dynamic>> get(String path) => _request('GET', path);

  Future<Response<dynamic>> post(String path, {Object? data, bool authenticate = true}) =>
      _request('POST', path, data: data, authenticate: authenticate);

  Future<Response<dynamic>> put(String path, {Object? data}) =>
      _request('PUT', path, data: data);

  Future<Response<dynamic>> _request(
    String method,
    String path, {
    Object? data,
    bool authenticate = true,
    bool retrying = false,
  }) async {
    final headers = <String, dynamic>{};
    if (authenticate) {
      final token = await StorageService.instance.getToken();
      if (token != null && token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    try {
      return await _dio.request<dynamic>(
        path,
        data: data,
        options: Options(method: method, headers: headers),
      );
    } on DioException catch (error) {
      if (authenticate && !retrying && error.response?.statusCode == 401) {
        final refreshed = await TokenManager.instance.refreshAccessToken();
        if (refreshed) {
          return _request(method, path, data: data, authenticate: authenticate, retrying: true);
        }
      }
      throw ApiException(_message(error), error.response?.statusCode);
    }
  }

  String _message(DioException error) {
    final body = error.response?.data;
    if (body is Map && body['detail'] is String) return body['detail'] as String;
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.connectionError) {
      return 'Cannot reach ECHO-ASSIST. Check the server address and connection.';
    }
    return 'Request failed${error.response?.statusCode == null ? '' : ' (${error.response!.statusCode})'}.';
  }
}
