import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Service for secure storage of tokens and preferences
class StorageService {
  static late StorageService _instance;
  late FlutterSecureStorage _secureStorage;
  late SharedPreferences _prefs;

  StorageService._internal();

  factory StorageService() {
    return _instance;
  }

  static Future<StorageService> initialize() async {
    _instance = StorageService._internal();
    _instance._secureStorage = const FlutterSecureStorage();
    _instance._prefs = await SharedPreferences.getInstance();
    return _instance;
  }

  // ===== Token Storage =====

  Future<void> saveToken(String token) async {
    await _secureStorage.write(key: 'auth_token', value: token);
  }

  Future<String?> getToken() async {
    return await _secureStorage.read(key: 'auth_token');
  }

  Future<void> deleteToken() async {
    await _secureStorage.delete(key: 'auth_token');
  }

  // ===== User Preferences =====

  Future<void> saveRememberMe(bool remember) async {
    await _prefs.setBool('remember_me', remember);
  }

  bool getRememberMe() {
    return _prefs.getBool('remember_me') ?? false;
  }

  Future<void> saveEmail(String email) async {
    await _prefs.setString('saved_email', email);
  }

  String? getSavedEmail() {
    return _prefs.getString('saved_email');
  }

  Future<void> clearAll() async {
    await _secureStorage.deleteAll();
    await _prefs.clear();
  }
}
