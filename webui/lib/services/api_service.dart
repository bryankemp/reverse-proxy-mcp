import 'dart:convert';
import 'dart:html' as html; // For web redirect on auth failures
import 'package:dio/dio.dart';
import 'package:logger/logger.dart';
import '../config/app_config.dart';
import '../models/models.dart';
import 'storage_service.dart';

/// Exception for API errors
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final dynamic originalError;

  ApiException({required this.message, this.statusCode, this.originalError});

  @override
  String toString() => 'ApiException: $message (Status: $statusCode)';
}

/// HTTP API Service with Dio
class ApiService {
  late Dio _dio;
  final StorageService _storage;
  final Logger _logger = Logger();
  static late ApiService _instance;

  ApiService._internal(this._storage) {
    _initializeDio();
    // Preload any stored token into headers to avoid race conditions
    // with interceptors on the first request after app start.
    // Intentionally not awaited; interceptor also fetches if still pending.
    // ignore: discarded_futures
    loadStoredToken();
  }

  factory ApiService(StorageService storage) {
    _instance = ApiService._internal(storage);
    return _instance;
  }

  static ApiService get instance => _instance;

  void _initializeDio() {
    final baseOptions = BaseOptions(
      baseUrl: AppConfig.getApiBaseUrl(),
      connectTimeout: Duration(milliseconds: AppConfig.connectionTimeout),
      receiveTimeout: Duration(milliseconds: AppConfig.receiveTimeout),
      sendTimeout: Duration(milliseconds: AppConfig.sendTimeout),
      contentType: 'application/json',
      responseType: ResponseType.json,
    );

    _dio = Dio(baseOptions);

    // Set default headers if token already persisted (best-effort)
    // This ensures even the very first request after app start carries the token
    // once loadStoredToken resolves.

    // Add logging interceptor if enabled
    if (AppConfig.enableLogging) {
      _dio.interceptors.add(LoggingInterceptor(_logger));
    }

    // Add auth interceptor
    _dio.interceptors.add(AuthInterceptor(_storage));
  }

  /// Set authorization token
  Future<void> setToken(String token) async {
    await _storage.saveToken(token);
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  /// Clear authentication
  Future<void> clearAuth() async {
    await _storage.deleteToken();
    _dio.options.headers.remove('Authorization');
  }

  /// Load token from storage and set in headers
  Future<void> loadStoredToken() async {
    final token = await _storage.getToken();
    if (token != null && token.isNotEmpty) {
      _dio.options.headers['Authorization'] = 'Bearer $token';
    }
  }

  // ===== Auth Endpoints =====

  /// Login with email and password
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post(
        '/auth/login',
        data: {'username': email, 'password': password},
      );
      return response.data;
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Login failed',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Logout
  Future<void> logout() async {
    try {
      await _dio.post('/auth/logout');
    } on DioException catch (e) {
      _logger.w('Logout failed: ${e.message}');
    }
  }

  // ===== Backend Endpoints =====

  /// List all backends
  Future<List<BackendServer>> listBackends({
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final response = await _dio.get(
        '/backends',
        queryParameters: {'limit': limit, 'offset': offset},
      );
      final list = response.data as List;
      return list
          .map((item) => BackendServer.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch backends',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Get backend by ID
  Future<BackendServer> getBackend(int id) async {
    try {
      final response = await _dio.get('/backends/$id');
      return BackendServer.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch backend',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Create backend
  Future<BackendServer> createBackend({
    required String name,
    required String host,
    required int port,
    String protocol = 'http',
    String description = '',
  }) async {
    try {
      final response = await _dio.post(
        '/backends',
        data: {
          'name': name,
          // Backend expects 'ip'
          'ip': host,
          'port': port,
          // Do not send unsupported fields to avoid 422
          // 'protocol': protocol,
          'service_description': description,
        },
      );
      return BackendServer.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to create backend',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Update backend
  Future<BackendServer> updateBackend(int id, BackendServer backend) async {
    try {
      final response = await _dio.put('/backends/$id', data: backend.toJson());
      return BackendServer.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to update backend',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Deactivate backend (marks as inactive)
  Future<void> deactivateBackend(int id) async {
    try {
      await _dio.post('/backends/$id/deactivate');
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to deactivate backend',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Delete backend (permanently removes from database)
  Future<void> deleteBackend(int id) async {
    try {
      await _dio.delete('/backends/$id');
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to delete backend',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  // ===== Proxy Rule Endpoints =====

  /// List all proxy rules
  Future<List<ProxyRule>> listProxyRules({
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final response = await _dio.get(
        '/proxy-rules',
        queryParameters: {'limit': limit, 'offset': offset},
      );
      final list = response.data as List;
      return list
          .map((item) => ProxyRule.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch proxy rules',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Get proxy rule by ID
  Future<ProxyRule> getProxyRule(int id) async {
    try {
      final response = await _dio.get('/proxy-rules/$id');
      return ProxyRule.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch proxy rule',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Create proxy rule
  Future<ProxyRule> createProxyRule({
    required String domain,
    required int backendId,
    String pathPattern = '/',
    String ruleType = 'reverse_proxy',
    int? certificateId,
    bool enableHsts = false,
    bool forceHttps = true,
    bool sslEnabled = true,
    String? rateLimit,
    String? ipWhitelist,
  }) async {
    try {
      final data = {
        'frontend_domain': domain,
        'backend_id': backendId,
        'path_pattern': pathPattern,
        'rule_type': ruleType,
        'enable_hsts': enableHsts,
        'force_https': forceHttps,
        'ssl_enabled': sslEnabled,
      };

      // Add optional fields only if provided
      if (certificateId != null) {
        data['certificate_id'] = certificateId;
      }
      if (rateLimit != null && rateLimit.isNotEmpty) {
        data['rate_limit'] = rateLimit;
      }
      if (ipWhitelist != null && ipWhitelist.isNotEmpty) {
        data['ip_whitelist'] = ipWhitelist;
      }

      final response = await _dio.post('/proxy-rules', data: data);
      return ProxyRule.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to create proxy rule',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Update proxy rule
  Future<ProxyRule> updateProxyRule(int id, ProxyRule rule) async {
    try {
      final response = await _dio.put('/proxy-rules/$id', data: rule.toJson());
      return ProxyRule.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to update proxy rule',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Deactivate proxy rule (marks as inactive)
  Future<void> deactivateProxyRule(int id) async {
    try {
      await _dio.post('/proxy-rules/$id/deactivate');
    } on DioException catch (e) {
      throw ApiException(
        message:
            e.response?.data?['detail'] ?? 'Failed to deactivate proxy rule',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Delete proxy rule (permanently removes from database)
  Future<void> deleteProxyRule(int id) async {
    try {
      await _dio.delete('/proxy-rules/$id');
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to delete proxy rule',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Reload Nginx
  Future<void> reloadNginx() async {
    try {
      await _dio.post('/config/reload');
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to reload Nginx',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  // ===== Certificate Endpoints =====

  /// List all certificates
  Future<List<Certificate>> listCertificates({
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final response = await _dio.get(
        '/certificates',
        queryParameters: {'limit': limit, 'offset': offset},
      );
      final list = response.data as List;
      return list
          .map((item) => Certificate.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch certificates',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Get certificate by ID
  Future<Certificate> getCertificate(int id) async {
    try {
      final response = await _dio.get('/certificates/$id');
      return Certificate.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch certificate',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Create certificate (multipart form upload)
  Future<Certificate> createCertificate({
    required String name,
    required String domain,
    required String certificatePem,
    required String privateKeyPem,
    bool isDefault = false,
    String? certFileName,
    String? keyFileName,
  }) async {
    try {
      final form = FormData.fromMap({
        'name': name,
        'domain': domain,
        'is_default': isDefault,
        'cert_file': MultipartFile.fromBytes(
          utf8.encode(certificatePem),
          filename: (certFileName == null || certFileName.isEmpty)
              ? 'certificate.pem'
              : certFileName,
        ),
        'key_file': MultipartFile.fromBytes(
          utf8.encode(privateKeyPem),
          filename: (keyFileName == null || keyFileName.isEmpty)
              ? 'private.key'
              : keyFileName,
        ),
      });
      final response = await _dio.post('/certificates', data: form);
      return Certificate.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to create certificate',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Set certificate as default
  Future<Certificate> setDefaultCertificate(int id) async {
    try {
      final response = await _dio.put('/certificates/$id/set-default');
      return Certificate.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message:
            e.response?.data?['detail'] ?? 'Failed to set default certificate',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Delete certificate
  Future<void> deleteCertificate(int id) async {
    try {
      await _dio.delete('/certificates/$id');
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to delete certificate',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  // ===== User Management Endpoints =====

  /// List all users
  Future<List<User>> listUsers({int limit = 50, int offset = 0}) async {
    try {
      final response = await _dio.get(
        '/users',
        queryParameters: {'limit': limit, 'offset': offset},
      );
      final list = response.data as List;
      return list
          .map((item) => User.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch users',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Get user by ID
  Future<User> getUser(int id) async {
    try {
      final response = await _dio.get('/users/$id');
      return User.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch user',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Create new user
  Future<User> createUser({
    required String username,
    required String email,
    required String password,
    String role = 'user',
    String? fullName,
  }) async {
    try {
      final data = {
        'username': username,
        'email': email,
        'password': password,
        'role': role,
      };
      if (fullName != null && fullName.isNotEmpty) {
        data['full_name'] = fullName;
      }
      final response = await _dio.post('/users', data: data);
      return User.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to create user',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Update user
  Future<User> updateUser(
    int id, {
    String? username,
    String? email,
    String? role,
    String? fullName,
    bool? isActive,
  }) async {
    try {
      final data = <String, dynamic>{};
      if (username != null) data['username'] = username;
      if (email != null) data['email'] = email;
      if (role != null) data['role'] = role;
      if (fullName != null) data['full_name'] = fullName;
      if (isActive != null) data['is_active'] = isActive;

      final response = await _dio.put('/users/$id', data: data);
      return User.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to update user',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Delete user
  Future<void> deleteUser(int id) async {
    try {
      await _dio.delete('/users/$id');
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to delete user',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Change password
  Future<void> changePassword({
    String? oldPassword,
    required String newPassword,
  }) async {
    try {
      final data = {'new_password': newPassword};
      if (oldPassword != null && oldPassword.isNotEmpty) {
        data['old_password'] = oldPassword;
      }
      await _dio.post('/auth/change-password', data: data);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to change password',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  // ===== Health & Metrics Endpoints =====

  /// Get system health status
  Future<HealthStatus> getHealth() async {
    try {
      final response = await _dio.get('/health');
      return HealthStatus.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch health',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Get metrics
  Future<List<Metrics>> getMetrics({
    String metricType = 'requests',
    int limit = 100,
  }) async {
    try {
      final response = await _dio.get(
        '/metrics',
        queryParameters: {'metric_type': metricType, 'limit': limit},
      );
      final list = response.data as List;
      return list
          .map((item) => Metrics.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch metrics',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Get current nginx configuration
  Future<String> getNginxConfig() async {
    try {
      final response = await _dio.get('/config/nginx');
      // If the response is a string, return it directly
      if (response.data is String) {
        return response.data as String;
      }
      // If it's a JSON object with a config field
      if (response.data is Map && response.data['config'] != null) {
        return response.data['config'] as String;
      }
      return response.data.toString();
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch nginx config',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  /// Get system logs
  Future<String> getLogs({int lines = 1000}) async {
    try {
      final response = await _dio.get(
        '/config/logs',
        queryParameters: {'lines': lines},
      );
      // If the response is a string, return it directly
      if (response.data is String) {
        return response.data as String;
      }
      // If it's a JSON object with a logs field
      if (response.data is Map && response.data['logs'] != null) {
        return response.data['logs'] as String;
      }
      return response.data.toString();
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch logs',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }
}

/// Logging interceptor for Dio
class LoggingInterceptor extends Interceptor {
  final Logger logger;

  LoggingInterceptor(this.logger);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    logger.d('REQUEST: ${options.method} ${options.path}', error: options.data);
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    logger.d(
      'RESPONSE: ${response.statusCode} ${response.requestOptions.path}',
      error: response.data,
    );
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    logger.e(
      'ERROR: ${err.requestOptions.path}',
      error: err.response?.data ?? err.message,
    );
    handler.next(err);
  }
}

/// Auth interceptor to add token to requests
class AuthInterceptor extends Interceptor {
  final StorageService storage;

  AuthInterceptor(this.storage);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await storage.getToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final status = err.response?.statusCode ?? 0;
    if (status == 401) {
      // Unknown/expired user → clear session and redirect to login
      try {
        await storage.deleteToken();
      } catch (_) {}
      // Force reload to root; AppRouter will present LoginScreen
      // Use replaceState to avoid back navigation loop
      html.window.location.assign('/');
      return; // Stop further handling
    }
    super.onError(err, handler);
  }
}
