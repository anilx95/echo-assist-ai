import 'package:flutter/material.dart';

class NavigationScreen extends StatelessWidget {
  const NavigationScreen({super.key});

  Widget buildStatusCard(
    String title,
    String value,
    Color color,
    IconData icon,
  ) {
    return Card(
      child: ListTile(
        leading: Icon(
          icon,
          color: color,
        ),
        title: Text(title),
        subtitle: Text(
          value,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget buildBottomButton(
    IconData icon,
    String title,
  ) {
    return Column(
      children: [
        CircleAvatar(
          radius: 28,
          child: Icon(icon),
        ),
        const SizedBox(height: 8),
        Text(title),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("AI Navigation"),
        centerTitle: true,
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),

        child: Column(
          children: [

            // Camera Preview Placeholder
            Container(
              height: 260,
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius:
                    BorderRadius.circular(16),
              ),
              child: const Center(
                child: Column(
                  mainAxisAlignment:
                      MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.camera_alt,
                      color: Colors.white,
                      size: 60,
                    ),
                    SizedBox(height: 15),
                    Text(
                      "Live Camera Preview",
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            buildStatusCard(
              "AI Status",
              "Connected",
              Colors.green,
              Icons.memory,
            ),

            buildStatusCard(
              "Bluetooth",
              "Disconnected",
              Colors.orange,
              Icons.bluetooth,
            ),

            buildStatusCard(
              "Detected Objects",
              "No Objects",
              Colors.blue,
              Icons.visibility,
            ),

            buildStatusCard(
              "Voice Guidance",
              "Waiting...",
              Colors.deepPurple,
              Icons.volume_up,
            ),

            const SizedBox(height: 25),

            const Divider(),

            const SizedBox(height: 15),

            Row(
              mainAxisAlignment:
                  MainAxisAlignment.spaceEvenly,
              children: [

                buildBottomButton(
                  Icons.camera_alt,
                  "Camera",
                ),

                buildBottomButton(
                  Icons.bluetooth,
                  "Bluetooth",
                ),

                buildBottomButton(
                  Icons.warning,
                  "SOS",
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}