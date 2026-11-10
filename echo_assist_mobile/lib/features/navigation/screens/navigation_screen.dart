import 'package:flutter/material.dart';

import '../../../services/api_service.dart';

class NavigationScreen extends StatefulWidget {
  const NavigationScreen({super.key});

  @override
  State<NavigationScreen> createState() => _NavigationScreenState();
}

class _NavigationScreenState extends State<NavigationScreen> {
  final _destination = TextEditingController();
  final _originLat = TextEditingController();
  final _originLng = TextEditingController();
  final _destinationLat = TextEditingController();
  final _destinationLng = TextEditingController();
  Map<String, dynamic>? _route;
  String? _error;
  bool _loading = false;

  @override
  void dispose() {
    for (final controller in [_destination, _originLat, _originLng, _destinationLat, _destinationLng]) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _requestRoute() async {
    if (_destination.text.trim().isEmpty) return;
    final body = <String, dynamic>{'destination': _destination.text.trim()};
    final fields = {
      'origin_latitude': _originLat.text,
      'origin_longitude': _originLng.text,
      'destination_latitude': _destinationLat.text,
      'destination_longitude': _destinationLng.text,
    };
    for (final entry in fields.entries) {
      if (entry.value.trim().isNotEmpty) {
        final value = double.tryParse(entry.value.trim());
        if (value == null) {
          setState(() => _error = 'Coordinates must be valid decimal numbers.');
          return;
        }
        body[entry.key] = value;
      }
    }
    setState(() { _loading = true; _error = null; });
    try {
      final response = await ApiService.instance.post('/navigation/route', data: body);
      setState(() => _route = Map<String, dynamic>.from(response.data as Map));
    } on ApiException catch (error) {
      setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Widget _coordinate(String label, TextEditingController controller) => Expanded(
    child: TextField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
      decoration: InputDecoration(labelText: label),
    ),
  );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Walking navigation')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Directions are returned only by a configured routing provider. ECHO-ASSIST never invents walking directions.'),
          const SizedBox(height: 16),
          TextField(controller: _destination, decoration: const InputDecoration(labelText: 'Destination name')),
          const SizedBox(height: 12),
          Row(children: [_coordinate('Current latitude', _originLat), const SizedBox(width: 12), _coordinate('Current longitude', _originLng)]),
          const SizedBox(height: 12),
          Row(children: [_coordinate('Destination latitude', _destinationLat), const SizedBox(width: 12), _coordinate('Destination longitude', _destinationLng)]),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _loading ? null : _requestRoute,
            child: _loading ? const CircularProgressIndicator() : const Text('Get provider route'),
          ),
          if (_error != null) Padding(padding: const EdgeInsets.only(top: 16), child: Text(_error!, style: const TextStyle(color: Colors.red))),
          if (_route != null) ...[
            const SizedBox(height: 20),
            Text('${_route!['destination']}', style: Theme.of(context).textTheme.titleLarge),
            Text('${_route!['total_distance_m']} m · about ${_route!['estimated_time_minutes']} minutes'),
            const SizedBox(height: 8),
            ...List<dynamic>.from(_route!['steps'] as List).map((item) {
              final step = Map<String, dynamic>.from(item as Map);
              return ListTile(
                leading: CircleAvatar(child: Text('${step['step_number']}')),
                title: Text(step['instruction']?.toString() ?? ''),
                subtitle: Text('${step['distance_m']} m'),
              );
            }),
          ],
        ],
      ),
    );
  }
}
