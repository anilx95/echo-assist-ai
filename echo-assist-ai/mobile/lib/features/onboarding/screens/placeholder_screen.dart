import 'package:flutter/material.dart';

/// Temporary placeholder for screens scheduled in later development phases
/// (see master prompt section 29). Keeps app navigation functional end to
/// end during Phase 1 without faking completed features.
class PlaceholderScreen extends StatelessWidget {
  const PlaceholderScreen({super.key, required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            '$title screen will be built in an upcoming development phase.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
        ),
      ),
    );
  }
}
