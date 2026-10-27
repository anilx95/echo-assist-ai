import 'package:flutter/material.dart';

import '../../../core/routes/route_names.dart';
import '../../../services/auth_service.dart';
import '../../../services/storage_service.dart';

class LoginController {
  final AuthService _authService = AuthService();

  Future<void> login({
    required BuildContext context,
    required String email,
    required String password,
  }) async {
    try {
      final user = await _authService.login(
        email: email,
        password: password,
      );

      await StorageService.instance.saveToken(
        user.accessToken,
      );

      await StorageService.instance.saveRefreshToken(
        user.refreshToken,
      );

      if (!context.mounted) return;

      Navigator.pushReplacementNamed(
        context,
        RouteNames.home,
      );
    } catch (e, stackTrace) {
      debugPrint("========== LOGIN ERROR ==========");
      debugPrint(e.toString());
      debugPrint(stackTrace.toString());

      if (!context.mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString()),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}