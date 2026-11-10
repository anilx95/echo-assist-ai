import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'app_colors.dart';

class AppTextStyles {
  AppTextStyles._();

  static TextStyle heading = GoogleFonts.syne(
    fontSize: 28,
    fontWeight: FontWeight.w800,
    color: AppColors.white,
    letterSpacing: -0.6,
  );

  static TextStyle title = GoogleFonts.syne(
    fontSize: 20,
    fontWeight: FontWeight.w700,
    color: AppColors.white,
    letterSpacing: -0.4,
  );

  static TextStyle body = GoogleFonts.inter(
    fontSize: 16,
    color: AppColors.grey,
    height: 1.5,
  );

  static TextStyle button = GoogleFonts.inter(
    fontSize: 16,
    fontWeight: FontWeight.w600,
    color: Colors.white,
    letterSpacing: -0.2,
  );
}
