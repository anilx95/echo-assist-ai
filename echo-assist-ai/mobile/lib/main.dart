import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/theme/app_theme.dart';
import 'core/services/voice_service.dart';
import 'features/home/providers/home_provider.dart';
import 'features/home/screens/home_screen.dart';
import 'features/onboarding/screens/placeholder_screen.dart';
import 'features/onboarding/screens/splash_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await VoiceService.instance.init();
  runApp(const EchoAssistApp());
}

class EchoAssistApp extends StatelessWidget {
  const EchoAssistApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => HomeProvider()),
      ],
      child: MaterialApp(
        title: 'ECHO-ASSIST AI',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        // Respect the user's OS text-scaling preference for accessibility,
        // clamped to a sane range so layouts don't break at extremes.
        builder: (context, child) {
          final mediaQuery = MediaQuery.of(context);
          final clampedScale = mediaQuery.textScaler.clamp(
            minScaleFactor: 1.0,
            maxScaleFactor: 1.6,
          );
          return MediaQuery(
            data: mediaQuery.copyWith(textScaler: clampedScale),
            child: child!,
          );
        },
        initialRoute: '/',
        routes: {
          '/': (context) => const SplashScreen(),
          '/onboarding/permissions': (context) =>
              const PlaceholderScreen(title: 'Permission Setup'),
          '/home': (context) => const HomeScreen(),
          '/live-assistance': (context) => const PlaceholderScreen(title: 'Live Assistance'),
          '/navigation': (context) => const PlaceholderScreen(title: 'Navigate'),
          '/scene-description': (context) =>
              const PlaceholderScreen(title: 'Describe Surroundings'),
          '/emergency': (context) => const PlaceholderScreen(title: 'Emergency SOS'),
          '/cane-connection': (context) =>
              const PlaceholderScreen(title: 'Connect Smart Cane'),
          '/settings': (context) => const PlaceholderScreen(title: 'Settings'),
        },
      ),
    );
  }
}
