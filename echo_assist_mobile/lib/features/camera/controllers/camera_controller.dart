import 'package:flutter/material.dart';

import '../services/camera_service.dart';

class CameraScreenController extends ChangeNotifier {
  bool _loading = true;

  bool get loading => _loading;

  Future<void> initializeCamera() async {
    _loading = true;
    notifyListeners();

    await CameraService.instance.initialize();

    _loading = false;
    notifyListeners();
  }

  Future<void> switchCamera() async {
    await CameraService.instance.switchCamera();
    notifyListeners();
  }

  @override
  void dispose() {
    CameraService.instance.dispose();
    super.dispose();
  }
}