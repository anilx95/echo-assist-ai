import 'package:flutter/material.dart';

/// Accessible Material 3 theme for ECHO-ASSIST AI.
///
/// Follows section 21 requirements: high contrast, large text support,
/// clear focus order, and no reliance on color alone to convey meaning
/// (icons + text labels are paired throughout the app).
class AppTheme {
  AppTheme._();

  // High-contrast palette. Dark background reduces glare and battery use;
  // bright accent colors carry semantic meaning (danger/warning/safe) but
  // are always paired with text/icons, never used alone.
  static const Color background = Color(0xFF0A0A0F);
  static const Color surface = Color(0xFF16161F);
  static const Color primary = Color(0xFF3DB2FF);
  static const Color onPrimary = Color(0xFF00131F);
  static const Color danger = Color(0xFFFF4D4D);
  static const Color warning = Color(0xFFFFB020);
  static const Color safe = Color(0xFF2ECC71);
  static const Color textPrimary = Color(0xFFF5F6FA);
  static const Color textSecondary = Color(0xFFB8BCC8);

  static ThemeData get darkTheme {
    final base = ThemeData(
      brightness: Brightness.dark,
      useMaterial3: true,
      colorScheme: const ColorScheme.dark(
        primary: primary,
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
            // Large, readable defaults. Users can scale further via OS
            // text-scaling settings, which this theme respects (no fixed
            // pixel overrides that block system accessibility scaling).
            headlineLarge: const TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: textPrimary,
            ),
            headlineMedium: const TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.bold,
              color: textPrimary,
            ),
            titleLarge: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w600,
              color: textPrimary,
            ),
            bodyLarge: const TextStyle(
              fontSize: 18,
              color: textPrimary,
            ),
            bodyMedium: const TextStyle(
              fontSize: 16,
              color: textSecondary,
            ),
          ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(double.infinity, 72), // large touch target
          backgroundColor: primary,
          foregroundColor: onPrimary,
          textStyle: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
      iconTheme: const IconThemeData(color: textPrimary, size: 32),
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
          borderRadius: BorderRadius.all(Radius.circular(20)),
        ),
      ),
      dividerColor: Colors.white12,
    );
  }

  /// Returns the semantic color for a risk level, always to be paired with
  /// text/icon (never the sole indicator) per accessibility requirements.
  static Color riskColor(String riskLevel) {
    switch (riskLevel.toUpperCase()) {
      case 'DANGER':
        return danger;
      case 'WARNING':
        return warning;
      case 'SAFE':
      default:
        return safe;
    }
  }
}
