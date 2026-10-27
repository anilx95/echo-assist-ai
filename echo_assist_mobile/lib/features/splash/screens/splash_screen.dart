import 'package:flutter/material.dart';

import '../../../core/routes/route_names.dart';
import '../../../services/storage_service.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() =>
      _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {

  @override
  void initState() {
    super.initState();
    _checkLogin();
  }

  Future<void> _checkLogin() async {

    final token =
        await StorageService.instance.getToken();

    // Keep splash visible for a moment
    await Future.delayed(
      const Duration(seconds: 2),
    );

    if (!mounted) return;

    Navigator.pushReplacementNamed(
      context,
      token != null
          ? RouteNames.home
          : RouteNames.login,
    );
  }

  @override
  Widget build(BuildContext context) {

    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: Column(
          mainAxisAlignment:
              MainAxisAlignment.center,
          children: [

            const Icon(
              Icons.visibility,
              color: Colors.blue,
              size: 90,
            ),

            const SizedBox(height: 25),

            const Text(
              "ECHO ASSIST AI",
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 30,
              ),
            ),

            const SizedBox(height: 10),

            const Text(
              "AI Powered Smart Navigation",
              style: TextStyle(
                color: Colors.grey,
                fontSize: 16,
              ),
            ),

            const SizedBox(height: 40),

            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}