import 'package:flutter/material.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';

/// Onboarding Screen 1 (section 4): logo and tagline.
class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Semantics(
                label: '${AppConstants.appName} logo',
                child: const Icon(
                  Icons.accessibility_new,
                  size: 96,
                  color: AppTheme.primary,
                ),
              ),
              const SizedBox(height: 24),
              Text(
                AppConstants.appName,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              const SizedBox(height: 12),
              Text(
                AppConstants.tagline,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: AppTheme.textSecondary,
                    ),
              ),
              const SizedBox(height: 48),
              ElevatedButton(
                onPressed: () => Navigator.of(context).pushReplacementNamed('/onboarding/permissions'),
                child: const Text('Get Started'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
