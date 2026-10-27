import 'package:flutter/material.dart';

import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/register_screen.dart';
import '../../features/bluetooth/screens/bluetooth_screen.dart';
import '../../features/camera/screens/camera_screen.dart';
import '../../features/emergency/screens/emergency_screen.dart';
import '../../features/home/screens/home_screen.dart';
import '../../features/navigation/screens/navigation_screen.dart';
import '../../features/profile/screens/profile_screen.dart';
import '../../features/settings/screens/settings_screen.dart';
import '../../features/splash/screens/splash_screen.dart';

import 'route_names.dart';

class AppRoutes {
  AppRoutes._();

  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      case RouteNames.splash:
        return MaterialPageRoute(
          builder: (_) => const SplashScreen(),
        );

      case RouteNames.login:
        return MaterialPageRoute(
          builder: (_) => const LoginScreen(),
        );

      case RouteNames.register:
        return MaterialPageRoute(
          builder: (_) => const RegisterScreen(),
        );

      case RouteNames.home:
        return MaterialPageRoute(
          builder: (_) => const HomeScreen(),
        );

      case RouteNames.camera:
        return MaterialPageRoute(
          builder: (_) => const CameraScreen(),
        );

      case RouteNames.navigation:
        return MaterialPageRoute(
          builder: (_) => const NavigationScreen(),
        );

      case RouteNames.bluetooth:
        return MaterialPageRoute(
          builder: (_) => const BluetoothScreen(),
        );

      case RouteNames.emergency:
        return MaterialPageRoute(
          builder: (_) => const EmergencyScreen(),
        );

      case RouteNames.settings:
        return MaterialPageRoute(
          builder: (_) => const SettingsScreen(),
        );

      case RouteNames.profile:
        return MaterialPageRoute(
          builder: (_) => const ProfileScreen(),
        );

      default:
        return MaterialPageRoute(
          builder: (_) => const SplashScreen(),
        );
    }
  }
}