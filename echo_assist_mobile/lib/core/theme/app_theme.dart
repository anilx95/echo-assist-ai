import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'app_colors.dart';

class AppTheme {
  AppTheme._();

  static ThemeData darkTheme = ThemeData(
    brightness: Brightness.dark,
    useMaterial3: true,

    scaffoldBackgroundColor: AppColors.background,

    colorScheme: const ColorScheme.dark(
      primary: AppColors.primary,
      secondary: AppColors.secondary,
      surface: AppColors.surface,
      error: AppColors.danger,
      onPrimary: Colors.white,
      onSurface: AppColors.white,
    ),

    textTheme: GoogleFonts.interTextTheme(
      ThemeData.dark().textTheme,
    ).copyWith(
      displayLarge: GoogleFonts.syne(
        fontSize: 34,
        fontWeight: FontWeight.w800,
        color: AppColors.white,
        letterSpacing: -0.8,
      ),
      headlineMedium: GoogleFonts.syne(
        fontSize: 24,
        fontWeight: FontWeight.w800,
        color: AppColors.white,
        letterSpacing: -0.5,
      ),
      headlineSmall: GoogleFonts.syne(
        fontSize: 20,
        fontWeight: FontWeight.w700,
        color: AppColors.white,
        letterSpacing: -0.3,
      ),
      titleLarge: GoogleFonts.syne(
        fontSize: 18,
        fontWeight: FontWeight.w700,
        color: AppColors.white,
      ),
      titleMedium: GoogleFonts.inter(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        color: AppColors.white,
      ),
      bodyLarge: GoogleFonts.inter(
        fontSize: 16,
        color: AppColors.white,
      ),
      bodyMedium: GoogleFonts.inter(
        fontSize: 14,
        color: AppColors.grey,
      ),
    ),

    appBarTheme: AppBarTheme(
      backgroundColor: AppColors.background,
      elevation: 0,
      centerTitle: true,
      titleTextStyle: GoogleFonts.syne(
        fontSize: 18,
        fontWeight: FontWeight.w800,
        color: AppColors.white,
        letterSpacing: -0.3,
      ),
      iconTheme: const IconThemeData(color: AppColors.white),
    ),

    cardTheme: CardThemeData(
      color: AppColors.surface,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.border, width: 1),
      ),
    ),

    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        minimumSize: const Size(double.infinity, 54),
        elevation: 0,
        shadowColor: AppColors.primary.withAlpha(100),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        textStyle: GoogleFonts.inter(
          fontSize: 15,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),

    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: const Color(0x0FFFFFFF),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: AppColors.primary, width: 1.5),
      ),
      labelStyle: const TextStyle(color: AppColors.grey),
      hintStyle: const TextStyle(color: Color(0x60E8ECF4)),
    ),

    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: AppColors.surface,
      selectedItemColor: AppColors.primary,
      unselectedItemColor: AppColors.grey,
    ),
  );
}
