import 'package:flutter_tts/flutter_tts.dart';

/// Priority levels for speech. Higher-priority speech interrupts lower.
/// Matches section 14: "Danger alerts must interrupt low-priority speech."
enum SpeechPriority { info, warning, danger }

/// Wraps flutter_tts with a simple priority model so obstacle danger alerts
/// always cut through scene descriptions or general chatter.
class VoiceService {
  VoiceService._internal() {
    _tts.setStartHandler(() => _isSpeaking = true);
    _tts.setCompletionHandler(() => _isSpeaking = false);
    _tts.setCancelHandler(() => _isSpeaking = false);
  }

  static final VoiceService instance = VoiceService._internal();
  final FlutterTts _tts = FlutterTts();

  bool _isSpeaking = false;
  SpeechPriority _currentPriority = SpeechPriority.info;

  Future<void> init({String language = 'en'}) async {
    await _tts.setLanguage(_localeFor(language));
    await _tts.setSpeechRate(0.5);
    await _tts.setVolume(1.0);
    await _tts.setPitch(1.0);
  }

  String _localeFor(String languageCode) {
    switch (languageCode) {
      case 'te':
        return 'te-IN';
      case 'hi':
        return 'hi-IN';
      case 'en':
      default:
        return 'en-US';
    }
  }

  /// Speaks [message]. If something lower-priority is already speaking and
  /// [priority] is higher, the current speech is interrupted immediately.
  Future<void> speak(String message, {SpeechPriority priority = SpeechPriority.info}) async {
    if (message.trim().isEmpty) return;

    final shouldInterrupt = _isSpeaking && priority.index > _currentPriority.index;
    if (_isSpeaking && !shouldInterrupt && priority.index <= _currentPriority.index) {
      // Lower or equal priority speech waits rather than interrupting.
      return;
    }

    if (shouldInterrupt) {
      await _tts.stop();
    }

    _currentPriority = priority;
    await _tts.speak(message);
  }

  Future<void> stop() async {
    await _tts.stop();
    _isSpeaking = false;
  }
}
