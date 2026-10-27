import 'package:flutter/material.dart';

import 'core/routes/app_routes.dart';
import 'core/routes/route_names.dart';
import 'core/theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  runApp(const EchoAssistApp());
}

class EchoAssistApp extends StatelessWidget {
  const EchoAssistApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,

      title: 'Echo Assist AI',

      theme: AppTheme.darkTheme,

      initialRoute: RouteNames.splash,

      onGenerateRoute: AppRoutes.generateRoute,
    );
  }
}