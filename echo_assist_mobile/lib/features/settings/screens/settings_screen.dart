import 'package:flutter/material.dart';

import '../../../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  Future<Map<String, dynamic>> _load() async {
    final response = await ApiService.instance.get('/devices/preferences/me');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<void> _save(Map<String, dynamic> values) async {
    await ApiService.instance.put('/devices/preferences/me', data: values);
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Settings saved.')));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Accessibility settings')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _load(),
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (snapshot.hasError) return Center(child: Text('${snapshot.error}'));
          final values = Map<String, dynamic>.from(snapshot.data!);
          return StatefulBuilder(builder: (context, setValues) => ListView(padding: const EdgeInsets.all(16), children: [
            const Text('Your choices are saved to your account.'),
            const SizedBox(height: 12),
            for (final item in <(String, String)>[
              ('voice_alerts_enabled', 'Enable voice alerts'),
              ('vibration_alerts_enabled', 'Enable vibration alerts'),
              ('high_contrast_mode', 'Use high contrast'),
              ('large_text_mode', 'Use large text'),
              ('fall_detection_enabled', 'Enable fall detection'),
            ])
              SwitchListTile(
                title: Text(item.$2),
                value: values[item.$1] == true,
                onChanged: (value) => setValues(() => values[item.$1] = value),
              ),
            const SizedBox(height: 16),
            FilledButton(onPressed: () => _save(values), child: const Text('Save settings')),
          ]));
        },
      ),
    );
  }
}
