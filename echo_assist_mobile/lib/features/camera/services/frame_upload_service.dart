import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../../core/constants/api_constants.dart';
import '../../../services/storage_service.dart';

class FrameUploadService {
  FrameUploadService._();

  static final FrameUploadService instance =
      FrameUploadService._();

  Future<Map<String, dynamic>> uploadFrame(
    String imagePath,
  ) async {
    final token =
        await StorageService.instance.getToken();

    print("========== FRAME UPLOAD ==========");
    print("Image Path: $imagePath");
    print("Token: $token");
    print("==================================");

    if (token == null || token.isEmpty) {
      throw Exception(
        "Access token not found. Please login again.",
      );
    }

    final request = http.MultipartRequest(
      "POST",
      Uri.parse(
        "${ApiConstants.baseUrl}/ai/pipeline/realtime-frame",
      ),
    );

    request.headers.addAll({
      "Authorization": "Bearer $token",
      "Accept": "application/json",
    });

    print("Headers:");
    print(request.headers);

    request.files.add(
      await http.MultipartFile.fromPath(
        "file",
        imagePath,
      ),
    );

    final streamedResponse =
        await request.send();

    final response =
        await http.Response.fromStream(
      streamedResponse,
    );

    print("========== RESPONSE ==========");
    print("Status Code: ${response.statusCode}");
    print(response.body);
    print("==============================");

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }

    throw Exception(
      "Status ${response.statusCode}\n${response.body}",
    );
  }
}