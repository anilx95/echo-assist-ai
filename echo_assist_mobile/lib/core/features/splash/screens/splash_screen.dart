import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/text_styles.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,

      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [

            const Icon(
              Icons.assistant_navigation,
              size: 90,
              color: AppColors.primary,
            ),

            const SizedBox(height: 25),

            Text(
              "Echo Assist AI",
              style: AppTextStyles.heading,
            ),

            const SizedBox(height: 12),

            Text(
              "AI Powered Smart Navigation",
              style: AppTextStyles.body,
            ),
          ],
        ),
      ),
    );
  }
}