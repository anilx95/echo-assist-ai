import 'package:flutter/material.dart';

import '../../../services/api_service.dart';

class BluetoothScreen extends StatefulWidget {
  const BluetoothScreen({super.key});

  @override
  State<BluetoothScreen> createState() => _BluetoothScreenState();
}

class _BluetoothScreenState extends State<BluetoothScreen> {
  final _deviceId = TextEditingController();
  final _deviceName = TextEditingController(text: 'ECHO-CANE');

  @override
  void dispose() {
    _deviceId.dispose();
    _deviceName.dispose();
    super.dispose();
  }

  Future<List<dynamic>> _load() async {
    final response = await ApiService.instance.get('/devices');
    return List<dynamic>.from(response.data as List);
  }

  Future<void> _register() async {
    if (_deviceId.text.trim().length < 3) return;
    try {
      await ApiService.instance.post('/devices', data: {
        'device_id': _deviceId.text.trim(),
        'device_name': _deviceName.text.trim().isEmpty ? 'ECHO-CANE' : _deviceName.text.trim(),
        'is_simulator': false,
      });
      _deviceId.clear();
      if (mounted) setState(() {});
    } on ApiException catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My smart cane')),
      body: FutureBuilder<List<dynamic>>(
        future: _load(),
        builder: (context, snapshot) => ListView(padding: const EdgeInsets.all(16), children: [
          const Text('Register only a cane you own. Bluetooth pairing can be added after device registration.'),
          const SizedBox(height: 12),
          TextField(controller: _deviceId, decoration: const InputDecoration(labelText: 'Device ID')),
          TextField(controller: _deviceName, decoration: const InputDecoration(labelText: 'Display name')),
          const SizedBox(height: 12),
          FilledButton(onPressed: _register, child: const Text('Register smart cane')),
          const SizedBox(height: 24),
          Text('Registered devices', style: Theme.of(context).textTheme.titleLarge),
          if (snapshot.connectionState != ConnectionState.done)
            const Padding(padding: EdgeInsets.all(16), child: Center(child: CircularProgressIndicator()))
          else if (snapshot.hasError)
            Text('${snapshot.error}')
          else if (snapshot.data!.isEmpty)
            const Padding(padding: EdgeInsets.only(top: 12), child: Text('No smart cane is registered.'))
          else
            ...snapshot.data!.map((item) {
              final device = Map<String, dynamic>.from(item as Map);
              return Card(child: ListTile(
                leading: const Icon(Icons.bluetooth_connected),
                title: Text(device['device_name']?.toString() ?? 'ECHO-CANE'),
                subtitle: Text('${device['device_id']} · ${device['connection_status']}\nBattery: ${device['battery_percent'] ?? 'unavailable'}%'),
                isThreeLine: true,
              ));
            }),
        ]),
      ),
    );
  }
}
