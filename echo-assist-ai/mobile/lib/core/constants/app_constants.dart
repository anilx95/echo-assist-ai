/// App-wide constants for ECHO-ASSIST AI.
///
/// Keeping these centralized avoids magic strings/numbers scattered across
/// screens, and matches section 2 / 21 of the master spec (accessibility,
/// modular architecture).
library;

class AppConstants {
  AppConstants._();

  static const String appName = "ECHO-ASSIST AI";
  static const String tagline = "AI for Inclusive Mobility";

  /// Base URL for the FastAPI backend. Override via --dart-define in CI/CD:
  /// flutter run --dart-define=BACKEND_URL=https://api.example.com
  static const String backendUrl = String.fromEnvironment(
    'BACKEND_URL',
    defaultValue: 'http://10.0.2.2:8000', // Android emulator loopback to host
  );

  static const List<String> supportedLanguages = ['en', 'te', 'hi'];

  static const Map<String, String> languageNames = {
    'en': 'English',
    'te': 'తెలుగు (Telugu)',
    'hi': 'हिन्दी (Hindi)',
  };

  /// Minimum touch target size in logical pixels, per accessibility spec.
  static const double minTouchTargetSize = 64.0;

  /// Seconds the user has to cancel a possible-fall alert before SOS fires.
  static const int fallDetectionCountdownSeconds = 15;

  /// BLE service/characteristic UUIDs for the ECHO-CANE device.
  /// Placeholders - must match esp32_firmware/src/main.cpp definitions.
  static const String caneServiceUuid = "0000ec00-0000-1000-8000-00805f9b34fb";
  static const String caneSensorCharUuid = "0000ec01-0000-1000-8000-00805f9b34fb";
  static const String caneCommandCharUuid = "0000ec02-0000-1000-8000-00805f9b34fb";
  static const String caneDeviceNamePrefix = "ECHO_CANE";
}
