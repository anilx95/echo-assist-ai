import 'package:flutter/material.dart';

import '../../../services/api_service.dart';

class EmergencyScreen extends StatefulWidget {
  const EmergencyScreen({super.key});

  @override
  State<EmergencyScreen> createState() => _EmergencyScreenState();
}

class _EmergencyScreenState extends State<EmergencyScreen> {
  bool _sending = false;

  Future<List<dynamic>> _history() async {
    final response = await ApiService.instance.get('/emergency/history');
    return List<dynamic>.from(response.data as List);
  }

  Future<void> _trigger() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Activate SOS?'),
        content: const Text('This creates an emergency event and attempts to notify your registered contacts.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Activate SOS')),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _sending = true);
    try {
      await ApiService.instance.post('/emergency/trigger', data: {'event_type': 'MANUAL_SOS'});
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('SOS created. Review notification delivery status in the web dashboard.')),
      );
      setState(() {});
    } on ApiException catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.message)));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('SOS emergency')),
      body: FutureBuilder<List<dynamic>>(
        future: _history(),
        builder: (context, snapshot) => ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Card(
              color: Theme.of(context).colorScheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(children: [
                  const Icon(Icons.warning_amber_rounded, color: Colors.red, size: 60),
                  const SizedBox(height: 12),
                  const Text('Use only when you need help', textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    onPressed: _sending ? null : _trigger,
                    style: FilledButton.styleFrom(backgroundColor: Colors.red),
                    icon: _sending
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.sos),
                    label: const Text('Activate SOS'),
                  ),
                  const SizedBox(height: 8),
                  const Text('The app does not claim delivery unless a provider confirms it.', textAlign: TextAlign.center),
                ]),
              ),
            ),
            const SizedBox(height: 20),
            Text('Alert history', style: Theme.of(context).textTheme.titleLarge),
            if (snapshot.connectionState != ConnectionState.done)
              const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator()))
            else if (snapshot.hasError)
              Padding(padding: const EdgeInsets.only(top: 12), child: Text('${snapshot.error}'))
            else if (snapshot.data!.isEmpty)
              const Padding(padding: EdgeInsets.only(top: 12), child: Text('No emergency alerts recorded.'))
            else
              ...snapshot.data!.map((row) {
                final event = Map<String, dynamic>.from(row as Map);
                return Card(child: ListTile(
                  leading: const Icon(Icons.emergency),
                  title: Text(event['event_type']?.toString() ?? 'Emergency'),
                  subtitle: Text(event['created_at']?.toString() ?? ''),
                  trailing: Text(event['status']?.toString() ?? ''),
                ));
              }),
          ],
        ),
      ),
    );
  }
}
