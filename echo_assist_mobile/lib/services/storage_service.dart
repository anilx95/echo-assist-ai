import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class StorageService {
  StorageService._();

  static final StorageService instance = StorageService._();

  final FlutterSecureStorage _storage =
      const FlutterSecureStorage();

  static const _tokenKey = "access_token";
  static const _refreshTokenKey = "refresh_token";

  Future<void> saveToken(String token) async {
    await _storage.write(
      key: _tokenKey,
      value: token,
    );
  }

  Future<String?> getToken() async {
    return await _storage.read(
      key: _tokenKey,
    );
  }

  Future<void> saveRefreshToken(
      String token) async {
    await _storage.write(
      key: _refreshTokenKey,
      value: token,
    );
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(
      key: _refreshTokenKey,
    );
  }

  Future<void> logout() async {
    await _storage.deleteAll();
  }
}