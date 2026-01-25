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

  ApiException({
    required this.message,
    this.statusCode,
    this.originalError,
  });

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
  Future<List<BackendServer>> listBackends({int limit = 50, int offset = 0}) async {
    try {
      final response = await _dio.get(
        '/backends',
        queryParameters: {'limit': limit, 'offset': offset},
      );
      final list = response.data as List;
      return list.map((item) => BackendServer.fromJson(item as Map<String, dynamic>)).toList();
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
          'host': host,
          'port': port,
          'protocol': protocol,
          'description': description,
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

  /// Delete backend
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
  Future<List<ProxyRule>> listProxyRules({int limit = 50, int offset = 0}) async {
    try {
      final response = await _dio.get(
        '/proxy-rules',
        queryParameters: {'limit': limit, 'offset': offset},
      );
      final list = response.data as List;
      return list.map((item) => ProxyRule.fromJson(item as Map<String, dynamic>)).toList();
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
  }) async {
    try {
      final response = await _dio.post(
        '/proxy-rules',
        data: {
          'domain': domain,
          'backend_id': backendId,
          'path_pattern': pathPattern,
          'rule_type': ruleType,
        },
      );
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

  /// Delete proxy rule
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
  Future<List<Certificate>> listCertificates({int limit = 50, int offset = 0}) async {
    try {
      final response = await _dio.get(
        '/certificates',
        queryParameters: {'limit': limit, 'offset': offset},
      );
      final list = response.data as List;
      return list.map((item) => Certificate.fromJson(item as Map<String, dynamic>)).toList();
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
  Future<List<Metrics>> getMetrics({String metricType = 'requests', int limit = 100}) async {
    try {
      final response = await _dio.get(
        '/metrics',
        queryParameters: {'metric_type': metricType, 'limit': limit},
      );
      final list = response.data as List;
      return list.map((item) => Metrics.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException(
        message: e.response?.data?['detail'] ?? 'Failed to fetch metrics',
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
    logger.d(
      'REQUEST: ${options.method} ${options.path}',
      error: options.data,
    );
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
}
