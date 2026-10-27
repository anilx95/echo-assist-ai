import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';

import '../services/camera_service.dart';
import '../services/frame_upload_service.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
 State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  bool _loading = true;
  bool _uploading = false;

  String? _error;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      final status = await Permission.camera.request();

      if (!status.isGranted) {
        setState(() {
          _loading = false;
          _error = "Camera permission denied";
        });
        return;
      }

      await CameraService.instance.initialize();

      if (!mounted) return;

      setState(() {
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _loading = false;
        _error = e.toString();
      });

      debugPrint(e.toString());
    }
  }

  Future<void> _detectObjects() async {
    try {
      setState(() {
        _uploading = true;
      });

      final controller = CameraService.instance.controller;

      if (controller == null) {
        throw Exception("Camera not initialized");
      }

      final XFile image = await controller.takePicture();

      debugPrint("Captured Image:");
      debugPrint(image.path);

      final result =
          await FrameUploadService.instance.uploadFrame(
        image.path,
      );

      debugPrint("============== AI RESPONSE ==============");
      debugPrint(result.toString());
      debugPrint("=========================================");

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("AI Detection Completed"),
        ),
      );
    } catch (e) {
      debugPrint(e.toString());

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: Colors.red,
          content: Text(e.toString()),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _uploading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    CameraService.instance.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final CameraController? controller =
        CameraService.instance.controller;

    return Scaffold(
      appBar: AppBar(
        title: const Text("AI Camera"),
      ),
      body: Builder(
        builder: (_) {
          if (_loading) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }

          if (_error != null) {
            return Center(
              child: Text(
                _error!,
                style: const TextStyle(color: Colors.red),
              ),
            );
          }

          if (controller == null ||
              !controller.value.isInitialized) {
            return const Center(
              child: Text("Camera not initialized"),
            );
          }

          return CameraPreview(controller);
        },
      ),
      floatingActionButton: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          FloatingActionButton.extended(
            heroTag: "detect",
            onPressed: _uploading ? null : _detectObjects,
            icon: _uploading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : const Icon(Icons.auto_awesome),
            label: const Text("AI Detect"),
          ),
          const SizedBox(height: 12),
          FloatingActionButton(
            heroTag: "flip",
            child: const Icon(Icons.flip_camera_android),
            onPressed: () async {
              try {
                await CameraService.instance.switchCamera();

                if (!mounted) return;

                setState(() {});
              } catch (e) {
                debugPrint(e.toString());
              }
            },
          ),
        ],
      ),
    );
  }
}