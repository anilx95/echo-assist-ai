import 'package:camera/camera.dart';

class CameraService {
  CameraService._();

  static final CameraService instance = CameraService._();

  CameraController? _controller;

  List<CameraDescription> _cameras = [];

  CameraController? get controller => _controller;

  Future<void> initialize({
    CameraLensDirection direction =
        CameraLensDirection.back,
  }) async {
    _cameras = await availableCameras();

    final selectedCamera = _cameras.firstWhere(
      (camera) => camera.lensDirection == direction,
      orElse: () => _cameras.first,
    );

    _controller = CameraController(
      selectedCamera,
      ResolutionPreset.medium,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.jpeg,
    );

    await _controller!.initialize();
  }

  Future<void> switchCamera() async {
    if (_controller == null) return;

    final currentDirection =
        _controller!.description.lensDirection;

    final newDirection =
        currentDirection == CameraLensDirection.back
            ? CameraLensDirection.front
            : CameraLensDirection.back;

    await dispose();

    await initialize(
      direction: newDirection,
    );
  }

  Future<void> dispose() async {
    await _controller?.dispose();
    _controller = null;
  }
}