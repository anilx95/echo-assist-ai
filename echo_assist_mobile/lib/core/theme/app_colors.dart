import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  // Primary & Accents (SaaS Platform Theme)
  static const Color primary = Color(0xFF8B5CF6); // Vibrant Purple / Violet
  static const Color primaryLight = Color(0xFFA78BFA); // Light Purple
  static const Color secondary = Color(0xFF06B6D4); // Cyan / Teal
  static const Color cyan = Color(0xFF06B6D4);

  // Background & Surfaces
  static const Color background = Color(0xFF06080F); // Deep space dark
  static const Color surface = Color(0xFF0C0F1A); // Dark slate surface
  static const Color surfaceElevated = Color(0xFF141A2E);
  static const Color border = Color(0x10FFFFFF); // Subtle hairline border

  // Text
  static const Color white = Color(0xFFE8ECF4);
  static const Color grey = Color(0xFF8E96A8);
  static const Color muted = Color(0x73E8ECF4);

  // Status
  static const Color success = Color(0xFF34D399); // Emerald pulse
  static const Color warning = Color(0xFFF59E0B);
  static const Color danger = Color(0xFFEF4444);

  // Navigation
  static const Color safe = Color(0xFF34D399);
  static const Color caution = Color(0xFFFACC15);
  static const Color obstacle = Color(0xFFEF4444);

  // Gradients
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [Color(0xFFA78BFA), Color(0xFF06B6D4)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}
