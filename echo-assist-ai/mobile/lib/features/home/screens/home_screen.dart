import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/services/voice_service.dart';
import '../../../core/theme/app_theme.dart';
import '../providers/home_provider.dart';

/// The main accessible home screen (section 5 of the master spec).
///
/// Large buttons, high contrast, minimal text, voice confirmation on major
/// actions. This screen intentionally avoids dense information display;
/// detailed status lives in the Developer Sensor Dashboard instead.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final home = context.watch<HomeProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('ECHO-ASSIST AI'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _StatusBar(home: home),
              const SizedBox(height: 20),
              Expanded(
                child: ListView(
                  children: [
                    _HomeActionButton(
                      label: 'Start Assistance',
                      icon: Icons.visibility,
                      semanticHint: 'Begins live obstacle detection and voice guidance',
                      onTap: () => _handleStartAssistance(context, home),
                    ),
                    const SizedBox(height: 16),
                    _HomeActionButton(
                      label: 'Navigate',
                      icon: Icons.navigation,
                      semanticHint: 'Get spoken directions to a destination',
                      onTap: () => _announceAndNavigate(context, '/navigation'),
                    ),
                    const SizedBox(height: 16),
                    _HomeActionButton(
                      label: 'Describe Surroundings',
                      icon: Icons.record_voice_over,
                      semanticHint: 'Hear a description of what is around you',
                      onTap: () => _announceAndNavigate(context, '/scene-description'),
                    ),
                    const SizedBox(height: 16),
                    _HomeActionButton(
                      label: 'Emergency SOS',
                      icon: Icons.sos,
                      isDanger: true,
                      semanticHint: 'Immediately alerts your emergency contacts with your location',
                      onTap: () => _announceAndNavigate(context, '/emergency'),
                    ),
                    const SizedBox(height: 16),
                    _HomeActionButton(
                      label: 'Connect Smart Cane',
                      icon: Icons.bluetooth,
                      semanticHint: 'Pair or reconnect to your ECHO-CANE device',
                      onTap: () => _announceAndNavigate(context, '/cane-connection'),
                    ),
                    const SizedBox(height: 16),
                    _HomeActionButton(
                      label: 'Settings',
                      icon: Icons.settings,
                      semanticHint: 'Change language, contacts, and preferences',
                      onTap: () => _announceAndNavigate(context, '/settings'),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _handleStartAssistance(BuildContext context, HomeProvider home) {
    final startingNow = !home.assistanceActive;
    home.setAssistanceActive(startingNow);
    VoiceService.instance.speak(
      startingNow ? 'Assistance mode started.' : 'Assistance mode stopped.',
      priority: SpeechPriority.warning,
    );
    if (startingNow) {
      Navigator.of(context).pushNamed('/live-assistance');
    }
  }

  void _announceAndNavigate(BuildContext context, String route) {
    Navigator.of(context).pushNamed(route);
  }
}

class _StatusBar extends StatelessWidget {
  const _StatusBar({required this.home});

  final HomeProvider home;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _StatusIcon(
              icon: Icons.accessibility_new,
              label: 'Cane',
              status: home.caneStatus,
            ),
            _StatusIcon(
              icon: Icons.gps_fixed,
              label: 'GPS',
              status: home.gpsStatus,
            ),
            _StatusIcon(
              icon: Icons.camera_alt,
              label: 'Camera',
              status: home.cameraStatus,
            ),
            _BatteryIndicator(percent: home.batteryPercent),
          ],
        ),
      ),
    );
  }
}

class _StatusIcon extends StatelessWidget {
  const _StatusIcon({required this.icon, required this.label, required this.status});

  final IconData icon;
  final String label;
  final ConnectionStatus status;

  Color _colorFor(ConnectionStatus status) {
    switch (status) {
      case ConnectionStatus.connected:
        return AppTheme.safe;
      case ConnectionStatus.connecting:
        return AppTheme.warning;
      case ConnectionStatus.disconnected:
      case ConnectionStatus.unavailable:
        return AppTheme.danger;
      case ConnectionStatus.unknown:
        return AppTheme.textSecondary;
    }
  }

  String _labelFor(ConnectionStatus status) {
    switch (status) {
      case ConnectionStatus.connected:
        return 'connected';
      case ConnectionStatus.connecting:
        return 'connecting';
      case ConnectionStatus.disconnected:
        return 'disconnected';
      case ConnectionStatus.unavailable:
        return 'unavailable';
      case ConnectionStatus.unknown:
        return 'unknown';
    }
  }

  @override
  Widget build(BuildContext context) {
    // Status is conveyed via color AND text label, never color alone.
    return Semantics(
      label: '$label status: ${_labelFor(status)}',
      child: Column(
        children: [
          Icon(icon, color: _colorFor(status)),
          const SizedBox(height: 4),
          Text(label, style: Theme.of(context).textTheme.bodyMedium),
        ],
      ),
    );
  }
}

class _BatteryIndicator extends StatelessWidget {
  const _BatteryIndicator({required this.percent});

  final double? percent;

  @override
  Widget build(BuildContext context) {
    final value = percent;
    final label = value == null ? 'unknown' : '${value.round()} percent';
    final color = value == null
        ? AppTheme.textSecondary
        : value < 20
            ? AppTheme.danger
            : AppTheme.safe;

    return Semantics(
      label: 'Battery: $label',
      child: Column(
        children: [
          Icon(Icons.battery_full, color: color),
          const SizedBox(height: 4),
          Text(
            value == null ? '--' : '${value.round()}%',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}

class _HomeActionButton extends StatelessWidget {
  const _HomeActionButton({
    required this.label,
    required this.icon,
    required this.onTap,
    required this.semanticHint,
    this.isDanger = false,
  });

  final String label;
  final IconData icon;
  final VoidCallback onTap;
  final String semanticHint;
  final bool isDanger;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: label,
      hint: semanticHint,
      child: ElevatedButton.icon(
        onPressed: onTap,
        icon: Icon(icon, size: 32),
        label: Align(
          alignment: Alignment.centerLeft,
          child: Text(label),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: isDanger ? AppTheme.danger : AppTheme.primary,
          foregroundColor: isDanger ? Colors.white : AppTheme.onPrimary,
          padding: const EdgeInsets.symmetric(horizontal: 24),
        ),
      ),
    );
  }
}
