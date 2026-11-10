import 'package:flutter/material.dart';

import '../../../core/routes/route_names.dart';
import '../../../services/api_service.dart';
import '../../../services/auth_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Future<Map<String, dynamic>> _load() async {
    final response = await ApiService.instance.get('/user/profile');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<void> _logout() async {
    await AuthService().logout();
    if (mounted) Navigator.pushNamedAndRemoveUntil(context, RouteNames.login, (route) => false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My profile')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _load(),
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (snapshot.hasError) return Center(child: Text('${snapshot.error}'));
          final profile = snapshot.data!;
          return ListView(padding: const EdgeInsets.all(20), children: [
            const CircleAvatar(radius: 42, child: Icon(Icons.person, size: 45)),
            const SizedBox(height: 16),
            Text(profile['full_name']?.toString() ?? '', textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineSmall),
            Text(profile['email']?.toString() ?? '', textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ListTile(leading: const Icon(Icons.verified_outlined), title: const Text('Email verification'),
                subtitle: Text(profile['is_verified'] == true ? 'Verified' : 'Not verified')),
            ListTile(leading: const Icon(Icons.phone_outlined), title: const Text('Phone number'),
                subtitle: Text(profile['phone_number']?.toString() ?? 'Not provided')),
            ListTile(leading: const Icon(Icons.language_outlined), title: const Text('Language'),
                subtitle: Text(profile['preferred_language']?.toString() ?? 'en')),
            const SizedBox(height: 24),
            OutlinedButton.icon(onPressed: _logout, icon: const Icon(Icons.logout), label: const Text('Sign out')),
          ]);
        },
      ),
    );
  }
}
