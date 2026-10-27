import 'package:flutter/material.dart';

import '../../../core/routes/route_names.dart';
import '../../../services/storage_service.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Profile"),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            const CircleAvatar(
              radius: 50,
              child: Icon(
                Icons.person,
                size: 55,
              ),
            ),

            const SizedBox(height: 20),

            const Text(
              "Echo Assist User",
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 8),

            const Text(
              "user@example.com",
            ),

            const SizedBox(height: 35),

            const ListTile(
              leading: Icon(Icons.info),
              title: Text("App Version"),
              subtitle: Text("1.0.0"),
            ),

            const ListTile(
              leading: Icon(Icons.language),
              title: Text("Language"),
              subtitle: Text("English"),
            ),

            const Spacer(),

            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.logout),
                label: const Text("Logout"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                ),
                onPressed: () async {
                  await StorageService.instance.logout();

                  if (!context.mounted) return;

                  Navigator.pushNamedAndRemoveUntil(
                    context,
                    RouteNames.login,
                    (route) => false,
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}