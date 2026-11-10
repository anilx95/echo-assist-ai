import 'package:flutter/material.dart';

import '../../../core/routes/route_names.dart';
import '../../../services/auth_service.dart';
import '../../../services/storage_service.dart';

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
      final tokens = await _authService.register(
        fullName: fullName,
        email: email,
        password: password,
        preferredLanguage: language,
      );

      if (!context.mounted) return;

      await StorageService.instance.saveToken(tokens.accessToken);
      await StorageService.instance.saveRefreshToken(tokens.refreshToken);
      if (!context.mounted) return;
      Navigator.pushNamedAndRemoveUntil(
        context,
        RouteNames.home,
        (route) => false,
      );
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
