import 'package:flutter/foundation.dart';

/// Connection/status states shown on the Home Dashboard (section 5) and used
/// to drive voice confirmations like "Smart cane connected."
enum ConnectionStatus { unknown, connecting, connected, disconnected, unavailable }

class HomeProvider extends ChangeNotifier {
  ConnectionStatus _caneStatus = ConnectionStatus.disconnected;
  ConnectionStatus _gpsStatus = ConnectionStatus.unknown;
  ConnectionStatus _cameraStatus = ConnectionStatus.unknown;
  double? _batteryPercent;
  bool _assistanceActive = false;

  ConnectionStatus get caneStatus => _caneStatus;
  ConnectionStatus get gpsStatus => _gpsStatus;
  ConnectionStatus get cameraStatus => _cameraStatus;
  double? get batteryPercent => _batteryPercent;
  bool get assistanceActive => _assistanceActive;

  void updateCaneStatus(ConnectionStatus status) {
    _caneStatus = status;
    notifyListeners();
  }

  void updateGpsStatus(ConnectionStatus status) {
    _gpsStatus = status;
    notifyListeners();
  }

  void updateCameraStatus(ConnectionStatus status) {
    _cameraStatus = status;
    notifyListeners();
  }

  void updateBattery(double percent) {
    _batteryPercent = percent;
    notifyListeners();
  }

  void setAssistanceActive(bool active) {
    _assistanceActive = active;
    notifyListeners();
  }
}
