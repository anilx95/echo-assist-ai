import 'dart:convert';

import 'package:http/http.dart' as http;

import '../core/constants/api_constants.dart';
import '../models/user_model.dart';

class AuthService {
  // ==========================
  // LOGIN
  // ==========================
  Future<UserModel> login({
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse(
        ApiConstants.baseUrl +
            ApiConstants.login,
      ),
      headers: {
        "Content-Type": "application/json",
      },
      body: jsonEncode({
        "email": email,
        "password": password,
      }),
    );

    if (response.statusCode == 200) {
      return UserModel.fromJson(
        jsonDecode(response.body),
      );
    }

    throw Exception(
      "Login Failed\n${response.body}",
    );
  }

  // ==========================
  // REGISTER
  // ==========================
  Future<void> register({
    required String fullName,
    required String email,
    required String password,
    required String preferredLanguage,
  }) async {
    final response = await http.post(
      Uri.parse(
        ApiConstants.baseUrl +
            ApiConstants.register,
      ),
      headers: {
        "Content-Type": "application/json",
      },
      body: jsonEncode({
        "full_name": fullName,
        "email": email,
        "password": password,
        "preferred_language":
            preferredLanguage,
      }),
    );

    if (response.statusCode == 200 ||
        response.statusCode == 201) {
      return;
    }

    throw Exception(
      "Registration Failed\n${response.body}",
    );
  }

  // ==========================
  // REFRESH TOKEN
  // ==========================
  Future<UserModel> refreshToken({
    required String refreshToken,
  }) async {
    final response = await http.post(
      Uri.parse(
        ApiConstants.baseUrl +
            ApiConstants.refresh,
      ),
      headers: {
        "Content-Type": "application/json",
      },
      body: jsonEncode({
        "refresh_token": refreshToken,
      }),
    );

    if (response.statusCode == 200) {
      return UserModel.fromJson(
        jsonDecode(response.body),
      );
    }

    throw Exception(
      "Refresh Token Failed\n${response.body}",
    );
  }
}