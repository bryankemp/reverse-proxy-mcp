import 'package:flutter/foundation.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';

/// Authentication state provider using ChangeNotifier pattern
class AuthProvider extends ChangeNotifier {
  final ApiService _apiService;
  final StorageService _storage;

  User? _currentUser;
  String? _token;
  bool _isLoading = false;
  String? _error;
  bool _isLoggedIn = false;

  // Getters
  User? get currentUser => _currentUser;
  String? get token => _token;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isLoggedIn => _isLoggedIn;
  bool get isAdmin => _currentUser?.isAdmin ?? false;

  AuthProvider(this._apiService, this._storage);

  /// Initialize auth state from stored token on app start
  Future<void> initializeStoredAuth() async {
    try {
      _setLoading(true);
      _clearError();

      // Try to load token from storage
      final storedToken = await _storage.getToken();
      if (storedToken != null && storedToken.isNotEmpty) {
        _token = storedToken;
        await _apiService.setToken(storedToken);

        // Optionally verify token is still valid by checking health
        try {
          final health = await _apiService.getHealth();
          if (health.isHealthy) {
            _isLoggedIn = true;
            notifyListeners();
            return;
          }
        } catch (e) {
          // Token might be expired, clear it
          await logout();
        }
      }

      _isLoggedIn = false;
      notifyListeners();
    } catch (e) {
      _setError('Failed to initialize authentication: $e');
    } finally {
      _setLoading(false);
    }
  }

  /// Login with email and password
  Future<bool> login({
    required String email,
    required String password,
    bool rememberMe = false,
  }) async {
    try {
      _setLoading(true);
      _clearError();

      // Call API login endpoint
      final response = await _apiService.login(
        email: email,
        password: password,
      );

      // Extract token from response
      final token = response['access_token'] as String?;
      if (token == null || token.isEmpty) {
        _setError('No token received from server');
        return false;
      }

      // Save token to storage
      _token = token;
      await _apiService.setToken(token);
      await _storage.saveToken(token);

      // Handle remember me (sanitize clearly bad values)
      final sanitized = email.trim();
      final looksCorrupted = sanitized.startsWith('Instance of');
      if (rememberMe && !looksCorrupted && sanitized.isNotEmpty) {
        await _storage.saveRememberMe(true);
        await _storage.saveEmail(sanitized);
      } else {
        await _storage.saveRememberMe(false);
      }

      // Extract user info from response
      final userData = response['user'] as Map<String, dynamic>?;
      if (userData != null) {
        _currentUser = User.fromJson(userData);
      }

      _isLoggedIn = true;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _setError(e.message);
      return false;
    } catch (e) {
      _setError('Login failed: $e');
      return false;
    } finally {
      _setLoading(false);
    }
  }

  /// Logout and clear authentication state
  Future<void> logout() async {
    try {
      _setLoading(true);

      // Call API logout endpoint
      await _apiService.logout();
    } catch (e) {
      // Log warning but continue with logout
      print('Logout API call failed: $e');
    }

    // Clear local state
    _token = null;
    _currentUser = null;
    _isLoggedIn = false;

    // Clear storage
    await _storage.deleteToken();
    await _apiService.clearAuth();

    _setLoading(false);
    notifyListeners();
  }

  /// Auto-login if remember me was enabled
  Future<bool> autoLogin() async {
    try {
      _setLoading(true);
      _clearError();

      final rememberMe = _storage.getRememberMe();
      if (!rememberMe) {
        _isLoggedIn = false;
        notifyListeners();
        return false;
      }

      final savedEmail = _storage.getSavedEmail();
      if (savedEmail == null || savedEmail.isEmpty) {
        _isLoggedIn = false;
        notifyListeners();
        return false;
      }

      // Try to use stored token
      final storedToken = await _storage.getToken();
      if (storedToken != null && storedToken.isNotEmpty) {
        _token = storedToken;
        await _apiService.setToken(storedToken);

        // Verify token is still valid
        try {
          final health = await _apiService.getHealth();
          if (health.isHealthy) {
            _isLoggedIn = true;
            notifyListeners();
            return true;
          }
        } catch (e) {
          // Token expired
          await logout();
          return false;
        }
      }

      _isLoggedIn = false;
      notifyListeners();
      return false;
    } catch (e) {
      _setError('Auto-login failed: $e');
      _isLoggedIn = false;
      notifyListeners();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  /// Refresh token (for future use)
  Future<bool> refreshToken() async {
    try {
      _setLoading(true);
      _clearError();

      // TODO: Implement refresh token endpoint in API
      // For now, if token is expired, user needs to login again
      _setError('Token refresh not yet implemented');
      return false;
    } catch (e) {
      _setError('Token refresh failed: $e');
      return false;
    } finally {
      _setLoading(false);
    }
  }

  /// Clear error message
  void clearError() {
    _clearError();
    notifyListeners();
  }

  // Private helper methods

  void _setLoading(bool loading) {
    _isLoading = loading;
  }

  void _clearError() {
    _error = null;
  }

  void _setError(String message) {
    _error = message;
  }
}
