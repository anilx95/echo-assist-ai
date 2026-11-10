import 'package:dio/dio.dart';

import '../../../services/api_service.dart';

class FrameUploadService {
  FrameUploadService._();

  static final FrameUploadService instance =
      FrameUploadService._();

  Future<Map<String, dynamic>> uploadFrame(
    String imagePath,
  ) async {
    final response = await ApiService.instance.post(
      '/ai/pipeline/realtime-frame',
      data: FormData.fromMap({
        'file': await MultipartFile.fromFile(imagePath),
      }),
    );
    return Map<String, dynamic>.from(response.data as Map);
  }
}
