import '../core/constants/api_constants.dart';
import '../models/user_model.dart';
import 'api_service.dart';
import 'storage_service.dart';

class AuthService {
  // ==========================
  // LOGIN
  // ==========================
  Future<UserModel> login({
    required String email,
    required String password,
  }) async {
    final response = await ApiService.instance.post(
      ApiConstants.login,
      data: {'email': email, 'password': password},
      authenticate: false,
    );
    return UserModel.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  // ==========================
  // REGISTER
  // ==========================
  Future<UserModel> register({
    required String fullName,
    required String email,
    required String password,
    required String preferredLanguage,
  }) async {
    final response = await ApiService.instance.post(
      ApiConstants.register,
      data: {
        'full_name': fullName,
        'email': email,
        'password': password,
        'preferred_language': preferredLanguage,
      },
      authenticate: false,
    );
    return UserModel.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  // ==========================
  // REFRESH TOKEN
  // ==========================
  Future<UserModel> refreshToken({
    required String refreshToken,
  }) async {
    final response = await ApiService.instance.post(
      ApiConstants.refresh,
      data: {'refresh_token': refreshToken},
      authenticate: false,
    );
    return UserModel.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  Future<void> logout() async {
    final refreshToken = await StorageService.instance.getRefreshToken();
    if (refreshToken != null) {
      try {
        await ApiService.instance.post(
          ApiConstants.logout,
          data: {'refresh_token': refreshToken},
          authenticate: false,
        );
      } on ApiException {
        // Local token removal is still required when the server is unreachable.
      }
    }
    await StorageService.instance.logout();
  }
}
