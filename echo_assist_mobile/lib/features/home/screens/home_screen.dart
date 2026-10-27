import 'package:flutter/material.dart';

import '../../../core/routes/route_names.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  Widget buildCard({
    required BuildContext context,
    required IconData icon,
    required String title,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: onTap,
      child: Card(
        elevation: 5,
        child: Container(
          height: 120,
          alignment: Alignment.center,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 45,
                color: color,
              ),
              const SizedBox(height: 12),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Echo Assist AI"),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.person),
            onPressed: () {
              Navigator.pushNamed(
                context,
                RouteNames.profile,
              );
            },
          ),
        ],
      ),

      body: Padding(
        padding: const EdgeInsets.all(16),
        child: GridView.count(
          crossAxisCount: 2,
          crossAxisSpacing: 15,
          mainAxisSpacing: 15,
          children: [

            buildCard(
              context: context,
              icon: Icons.camera_alt,
              title: "Camera",
              color: Colors.blue,
              onTap: () {
                Navigator.pushNamed(
                  context,
                  RouteNames.camera,
                );
              },
            ),

            buildCard(
              context: context,
              icon: Icons.navigation,
              title: "Navigation",
              color: Colors.green,
              onTap: () {
                Navigator.pushNamed(
                  context,
                  RouteNames.navigation,
                );
              },
            ),

            buildCard(
              context: context,
              icon: Icons.bluetooth,
              title: "Bluetooth",
              color: Colors.indigo,
              onTap: () {
                Navigator.pushNamed(
                  context,
                  RouteNames.bluetooth,
                );
              },
            ),

            buildCard(
              context: context,
              icon: Icons.mic,
              title: "Voice Assistant",
              color: Colors.orange,
              onTap: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text(
                      "Voice Assistant module coming soon",
                    ),
                  ),
                );
              },
            ),

            buildCard(
              context: context,
              icon: Icons.warning,
              title: "SOS",
              color: Colors.red,
              onTap: () {
                Navigator.pushNamed(
                  context,
                  RouteNames.emergency,
                );
              },
            ),

            buildCard(
              context: context,
              icon: Icons.settings,
              title: "Settings",
              color: Colors.grey,
              onTap: () {
                Navigator.pushNamed(
                  context,
                  RouteNames.settings,
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}