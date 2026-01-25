import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Service for secure storage of tokens and preferences
class StorageService {
  static late StorageService _instance;
  FlutterSecureStorage? _secureStorage; // nullable on web/insecure context
  late SharedPreferences _prefs;

  StorageService._internal();

  factory StorageService() {
    return _instance;
  }

  static Future<StorageService> initialize() async {
    _instance = StorageService._internal();
    // On web, flutter_secure_storage may crash in insecure contexts.
    // Use best-effort init and always keep a SharedPreferences fallback.
    try {
      if (!kIsWeb) {
        _instance._secureStorage = const FlutterSecureStorage();
      } else {
        // Web: defer creating secure storage; fallback to prefs for tokens.
        _instance._secureStorage = null;
      }
    } catch (_) {
      _instance._secureStorage = null;
    }
    _instance._prefs = await SharedPreferences.getInstance();
    return _instance;
  }

  // ===== Token Storage =====

  Future<void> saveToken(String token) async {
    // Prefer secure storage when available; otherwise fallback to prefs.
    try {
      if (_secureStorage != null) {
        await _secureStorage!.write(key: 'auth_token', value: token);
        return;
      }
    } catch (_) {/* ignore and fallback */}
    await _prefs.setString('auth_token', token);
  }

  Future<String?> getToken() async {
    try {
      if (_secureStorage != null) {
        final v = await _secureStorage!.read(key: 'auth_token');
        if (v != null && v.isNotEmpty) return v;
      }
    } catch (_) {/* ignore and fallback */}
    return _prefs.getString('auth_token');
  }

  Future<void> deleteToken() async {
    try {
      if (_secureStorage != null) {
        await _secureStorage!.delete(key: 'auth_token');
      }
    } catch (_) {/* ignore */}
    await _prefs.remove('auth_token');
  }

  // ===== User Preferences =====

  Future<void> saveRememberMe(bool remember) async {
    await _prefs.setBool('remember_me', remember);
  }

  bool getRememberMe() {
    return _prefs.getBool('remember_me') ?? false;
  }

  Future<void> saveEmail(String email) async {
    final v = email.trim();
    if (v.isEmpty || v.startsWith('Instance of')) {
      await _prefs.remove('saved_email');
      return;
    }
    await _prefs.setString('saved_email', v);
  }

  String? getSavedEmail() {
    return _prefs.getString('saved_email');
  }

  Future<void> clearAll() async {
    try {
      if (_secureStorage != null) {
        await _secureStorage!.deleteAll();
      }
    } catch (_) {/* ignore */}
    await _prefs.clear();
  }
}
