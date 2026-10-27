import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../constants/app_constants.dart';

/// Thin wrapper around Dio for all backend communication.
///
/// Centralizing this means BLE/location/AI features never need to know
/// about auth headers, base URLs, or error shapes directly - matching the
/// "clean architecture / separate API services" requirement in section 3.
class ApiService {
  ApiService._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.backendUrl,
        connectTimeout: const Duration(seconds: 8),
        receiveTimeout: const Duration(seconds: 8),
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _getAccessToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) {
          // Centralized place to handle 401s (token refresh) later.
          // For MVP we surface the error to the caller.
          handler.next(error);
        },
      ),
    );
  }

  static final ApiService instance = ApiService._internal();
  late final Dio _dio;

  static const _accessTokenKey = 'echo_assist_access_token';
  static const _refreshTokenKey = 'echo_assist_refresh_token';

  Future<String?> _getAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_accessTokenKey);
  }

  Future<void> saveTokens({required String accessToken, required String refreshToken}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_accessTokenKey, accessToken);
    await prefs.setString(_refreshTokenKey, refreshToken);
  }

  Future<void> clearTokens() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_accessTokenKey);
    await prefs.remove(_refreshTokenKey);
  }

  // --- Auth ---

  Future<Response> register({
    required String fullName,
    required String email,
    required String password,
    String preferredLanguage = 'en',
  }) {
    return _dio.post('/auth/register', data: {
      'full_name': fullName,
      'email': email,
      'password': password,
      'preferred_language': preferredLanguage,
    });
  }

  Future<Response> login({required String email, required String password}) {
    return _dio.post('/auth/login', data: {'email': email, 'password': password});
  }

  // --- Health ---

  Future<Response> healthCheck() => _dio.get('/health');

  // --- Contacts ---

  Future<Response> getContacts() => _dio.get('/contacts');

  Future<Response> createContact({
    required String name,
    required String relationshipType,
    required String phoneNumber,
    String? email,
  }) {
    return _dio.post('/contacts', data: {
      'name': name,
      'relationship_type': relationshipType,
      'phone_number': phoneNumber,
      if (email != null) 'email': email,
    });
  }

  // --- Sensors ---

  Future<Response> sendSensorData(Map<String, dynamic> packet) {
    return _dio.post('/sensors/data', data: packet);
  }

  Future<Response> getLatestSensorReading() => _dio.get('/sensors/latest');

  // --- AI ---

  Future<Response> detectObjects() => _dio.post('/ai/detect', data: {'use_mock': true});

  Future<Response> predictRisk({
    required String objectName,
    required double fusedDistanceM,
    String direction = 'center',
    bool isApproaching = false,
  }) {
    return _dio.post('/ai/risk', data: {
      'object_name': objectName,
      'fused_distance_m': fusedDistanceM,
      'direction': direction,
      'is_approaching': isApproaching,
    });
  }

  Future<Response> describeScene() {
    return _dio.post('/ai/scene-description', data: {'use_mock': true});
  }

  // --- Emergency ---

  Future<Response> triggerEmergency({
    required String eventType,
    required double latitude,
    required double longitude,
  }) {
    return _dio.post('/emergency/trigger', data: {
      'event_type': eventType,
      'latitude': latitude,
      'longitude': longitude,
    });
  }

  Future<Response> cancelEmergency(int emergencyId) {
    return _dio.post('/emergency/cancel', data: {'emergency_id': emergencyId});
  }

  // --- Navigation ---

  Future<Response> getRoute({
    required double originLat,
    required double originLng,
    required String destination,
  }) {
    return _dio.post('/navigation/route', data: {
      'origin_lat': originLat,
      'origin_lng': originLng,
      'destination': destination,
    });
  }
}
