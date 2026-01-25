/// Application configuration constants

class AppConfig {
  // API Configuration
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://window.location.host/api/v1',
  );
  
  /// Get API base URL dynamically based on current host
  static String getApiBaseUrl() {
    // If not using string.fromEnvironment, use current hostname
    return apiBaseUrl.contains('window.location') 
        ? '/api/v1'  // Relative path uses current domain
        : apiBaseUrl;
  }

  static const String appName = 'Nginx Manager';
  static const String appVersion = '1.0.0';

  // API Timeouts
  static const int connectionTimeout = 10000; // ms
  static const int receiveTimeout = 10000; // ms
  static const int sendTimeout = 10000; // ms

  // Storage Keys
  static const String tokenStorageKey = 'auth_token';
  static const String refreshTokenStorageKey = 'refresh_token';
  static const String userStorageKey = 'current_user';
  static const String rememberMeKey = 'remember_me';
  static const String userEmailKey = 'saved_email';

  // Token Configuration
  static const int tokenExpiryMinutes = 1440; // 24 hours

  // UI Configuration
  static const int pageSize = 20;
  static const int maxRetries = 3;
  static const int retryDelaySeconds = 2;

  // Features
  // Logging is disabled by default in release builds; can be enabled via --dart-define=APP_DEBUG=true
  static const bool enableLogging = bool.fromEnvironment('APP_DEBUG', defaultValue: false);
  static const bool enableAnalytics = false;

  // Roles
  static const String roleAdmin = 'admin';
  static const String roleUser = 'user';
}
