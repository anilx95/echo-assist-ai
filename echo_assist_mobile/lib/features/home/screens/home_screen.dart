import 'package:flutter/material.dart';

import '../../../core/routes/route_names.dart';
import '../../../core/theme/app_colors.dart';
import '../../../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Future<Map<String, dynamic>> _load() async {
    final response = await ApiService.instance.get('/dashboard/overview');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Widget _action(BuildContext context, IconData icon, String label, String route,
      {Color? color}) {
    final effectiveColor = color ?? AppColors.primary;
    return Semantics(
      button: true,
      label: label,
      child: Card(
        color: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.border, width: 1),
        ),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => Navigator.pushNamed(context, route),
          child: SizedBox(
            height: 112,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: effectiveColor.withAlpha(30),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: effectiveColor.withAlpha(64),
                      width: 1,
                    ),
                  ),
                  child: Icon(icon, size: 22, color: effectiveColor),
                ),
                const SizedBox(height: 10),
                Text(
                  label,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                    color: AppColors.white,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ECHO-ASSIST AI'),
        actions: [
          IconButton(
            tooltip: 'My profile',
            icon: const Icon(Icons.person_outline),
            onPressed: () => Navigator.pushNamed(context, RouteNames.profile),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => setState(() {}),
        child: FutureBuilder<Map<String, dynamic>>(
          future: _load(),
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return ListView(children: [
                const SizedBox(height: 96),
                Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text('Dashboard unavailable\n${snapshot.error}',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: AppColors.grey)),
                ),
              ]);
            }
            final data = snapshot.data!;
            final reading = data['latest_sensor_reading'] as Map?;
            final activeSos = data['active_sos'] as Map?;
            final risk = data['latest_risk'] as Map?;
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text('Your assistance status',
                    style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 12),
                Card(
                  child: ListTile(
                    leading: Container(
                      width: 38,
                      height: 38,
                      decoration: BoxDecoration(
                        color: (activeSos == null ? AppColors.success : AppColors.danger)
                            .withAlpha(30),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(
                        activeSos == null ? Icons.check_circle : Icons.warning,
                        color: activeSos == null ? AppColors.success : AppColors.danger,
                        size: 22,
                      ),
                    ),
                    title: Text(
                      activeSos == null ? 'No active SOS alert' : 'SOS alert is active',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    subtitle: Text(
                      risk?['message']?.toString() ?? 'No current obstacle-risk message.',
                      style: const TextStyle(color: AppColors.grey),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Card(
                  child: ListTile(
                    leading: Container(
                      width: 38,
                      height: 38,
                      decoration: BoxDecoration(
                        color: AppColors.secondary.withAlpha(30),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(
                        Icons.battery_std,
                        color: AppColors.secondary,
                        size: 22,
                      ),
                    ),
                    title: const Text('Latest smart-cane battery',
                        style: TextStyle(fontWeight: FontWeight.w600)),
                    subtitle: Text(
                      reading?['battery_percent'] == null
                          ? 'No sensor reading available'
                          : '${reading!['battery_percent']}%',
                      style: const TextStyle(color: AppColors.grey),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  children: [
                    _action(context, Icons.camera_alt_outlined, 'Camera', RouteNames.camera),
                    _action(context, Icons.navigation_outlined, 'Navigation', RouteNames.navigation),
                    _action(context, Icons.bluetooth_outlined, 'Smart cane', RouteNames.bluetooth),
                    _action(context, Icons.settings_outlined, 'Settings', RouteNames.settings),
                    _action(context, Icons.warning_amber_rounded, 'SOS emergency', RouteNames.emergency,
                        color: AppColors.danger),
                    _action(context, Icons.person_outline, 'My profile', RouteNames.profile),
                  ],
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
