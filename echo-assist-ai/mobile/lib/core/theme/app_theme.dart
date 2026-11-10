import 'package:flutter/material.dart';

/// Accessible Material 3 theme for ECHO-ASSIST AI (SaaS Platform Theme).
///
/// Follows modern SaaS design: Deep space background, dark slate surface,
/// vibrant purple (#8B5CF6) and cyan (#06B6D4) accents with high contrast.
class AppTheme {
  AppTheme._();

  static const Color background = Color(0xFF06080F);
  static const Color surface = Color(0xFF0C0F1A);
  static const Color primary = Color(0xFF8B5CF6);
  static const Color onPrimary = Colors.white;
  static const Color secondary = Color(0xFF06B6D4);
  static const Color danger = Color(0xFFEF4444);
  static const Color warning = Color(0xFFF59E0B);
  static const Color safe = Color(0xFF34D399);
  static const Color textPrimary = Color(0xFFE8ECF4);
  static const Color textSecondary = Color(0xFF8E96A8);

  static ThemeData get darkTheme {
    final base = ThemeData(
      brightness: Brightness.dark,
      useMaterial3: true,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: secondary,
        onPrimary: onPrimary,
        surface: surface,
        error: danger,
      ),
      scaffoldBackgroundColor: background,
    );

    return base.copyWith(
      textTheme: base.textTheme
          .apply(
            bodyColor: textPrimary,
            displayColor: textPrimary,
          )
          .copyWith(
            headlineLarge: const TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: textPrimary,
              letterSpacing: -0.8,
            ),
            headlineMedium: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: textPrimary,
              letterSpacing: -0.5,
            ),
            titleLarge: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: textPrimary,
            ),
            bodyLarge: const TextStyle(
              fontSize: 16,
              color: textPrimary,
            ),
            bodyMedium: const TextStyle(
              fontSize: 14,
              color: textSecondary,
            ),
          ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(double.infinity, 54),
          backgroundColor: primary,
          foregroundColor: onPrimary,
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
      ),
      iconTheme: const IconThemeData(color: textPrimary, size: 28),
      appBarTheme: const AppBarTheme(
        backgroundColor: background,
        foregroundColor: textPrimary,
        centerTitle: true,
        elevation: 0,
      ),
      cardTheme: const CardThemeData(
        color: surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(16)),
          side: BorderSide(color: Color(0x10FFFFFF), width: 1),
        ),
      ),
      dividerColor: Colors.white12,
    );
  }

  static Color colorForRisk(String? level) {
    switch (level?.toUpperCase()) {
      case 'DANGER':
        return danger;
      case 'WARNING':
        return warning;
      case 'SAFE':
        return safe;
      default:
        return textSecondary;
    }
  }
}
