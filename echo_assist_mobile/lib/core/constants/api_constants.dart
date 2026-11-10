import 'package:flutter/foundation.dart';

class ApiConstants {
  ApiConstants._();

  static const String _configured = String.fromEnvironment('API_BASE_URL');

  /// Dynamically resolves the base URL:
  /// - Environment override if provided via `--dart-define=API_BASE_URL=...`
  /// - `http://127.0.0.1:8000` for Web (Chrome, Edge) and Windows desktop
  /// - `http://10.0.2.2:8000` for Android emulator
  static String get baseUrl {
    if (_configured.isNotEmpty) return _configured;
    if (kIsWeb) return 'http://127.0.0.1:8000';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://127.0.0.1:8000';
  }

  static const String login = "/auth/login";
  static const String register = "/auth/register";
  static const String refresh = "/auth/refresh";
  static const String logout = "/auth/logout";
  static const String profile = "/user/profile";
  static const String dashboard = "/dashboard/overview";
  static const String emergencyTrigger = "/emergency/trigger";
  static const String emergencyHistory = "/emergency/history";
  static const String navigationRoute = "/navigation/route";
  static const String navigationHistory = "/navigation/history";
  static const String preferences = "/devices/preferences/me";
}
