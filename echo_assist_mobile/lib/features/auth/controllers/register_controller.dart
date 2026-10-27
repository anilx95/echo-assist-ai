import 'package:flutter/material.dart';

import '../../../services/auth_service.dart';

class RegisterController {
  final AuthService _authService =
      AuthService();

  Future<void> register({
    required BuildContext context,
    required String fullName,
    required String email,
    required String password,
    required String language,
  }) async {
    try {
      await _authService.register(
        fullName: fullName,
        email: email,
        password: password,
        preferredLanguage: language,
      );

      if (!context.mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(
        const SnackBar(
          content: Text(
            "Registration Successful",
          ),
        ),
      );

      Navigator.pop(context);
    } catch (e) {
      if (!context.mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(
        SnackBar(
          content: Text(
            e.toString(),
          ),
        ),
      );
    }
  }
}