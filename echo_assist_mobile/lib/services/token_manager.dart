import 'auth_service.dart';
import 'storage_service.dart';

class TokenManager {
  TokenManager._();

  static final instance = TokenManager._();

  final AuthService _authService = AuthService();

  Future<bool> refreshAccessToken() async {
    try {
      final refreshToken =
          await StorageService.instance.getRefreshToken();

      if (refreshToken == null) {
        return false;
      }

      final user =
          await _authService.refreshToken(
        refreshToken: refreshToken,
      );

      await StorageService.instance.saveToken(
        user.accessToken,
      );

      await StorageService.instance.saveRefreshToken(
        user.refreshToken,
      );

      return true;
    } catch (_) {
      await StorageService.instance.logout();
      return false;
    }
  }
}