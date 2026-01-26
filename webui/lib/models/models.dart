/// Dart models for Nginx Manager API responses

/// User model
class User {
  final int id;
  final String username;
  final String email;
  final String role; // 'admin' or 'user'
  final String fullName;
  final bool isActive;
  final DateTime createdAt;
  final DateTime updatedAt;

  User({
    required this.id,
    required this.username,
    required this.email,
    required this.role,
    required this.fullName,
    required this.isActive,
    required this.createdAt,
    required this.updatedAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int? ?? 0,
      username: json['username'] as String? ?? '',
      email: json['email'] as String? ?? '',
      role: json['role'] as String? ?? 'user',
      fullName: json['full_name'] as String? ?? '',
      isActive: json['is_active'] as bool? ?? true,
      createdAt: DateTime.parse(json['created_at'] as String? ?? DateTime.now().toIso8601String()),
      updatedAt: DateTime.parse(json['updated_at'] as String? ?? DateTime.now().toIso8601String()),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'username': username,
    'email': email,
    'role': role,
    'full_name': fullName,
    'is_active': isActive,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
  };

  bool get isAdmin => role == 'admin';
}

/// Backend Server model
class BackendServer {
  final int id;
  final String name;
  final String host;
  final int port;
  final String protocol; // 'http' or 'https'
  final String description;
  final bool isActive;
  final int createdBy;
  final DateTime createdAt;
  final DateTime updatedAt;

  BackendServer({
    required this.id,
    required this.name,
    required this.host,
    required this.port,
    required this.protocol,
    required this.description,
    required this.isActive,
    required this.createdBy,
    required this.createdAt,
    required this.updatedAt,
  });

  factory BackendServer.fromJson(Map<String, dynamic> json) {
    return BackendServer(
      id: json['id'] as int? ?? 0,
      name: json['name'] as String? ?? '',
      // Backend returns 'ip' not 'host'
      host: json['ip'] as String? ?? json['host'] as String? ?? '',
      port: json['port'] as int? ?? 8080,
      // Backend schema currently doesn't expose protocol; default to http
      protocol: (json['protocol'] as String?) ?? 'http',
      // Backend returns 'service_description'
      description: json['service_description'] as String? ?? json['description'] as String? ?? '',
      isActive: json['is_active'] as bool? ?? true,
      createdBy: json['created_by'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String? ?? DateTime.now().toIso8601String()),
      updatedAt: DateTime.parse(json['updated_at'] as String? ?? DateTime.now().toIso8601String()),
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    // Backend expects 'ip'
    'ip': host,
    'port': port,
    // Backend now accepts protocol
    'protocol': protocol,
    // Backend expects 'service_description'
    'service_description': description,
    // Include is_active for updates
    'is_active': isActive,
  };

  String get displayUrl => '$protocol://$host:$port';
}

/// Proxy Rule model
class ProxyRule {
  final int id;
  final String domain; // maps to backend 'frontend_domain'
  final int backendId;
  final String? accessControl;
  final String? ipWhitelist;
  // Optional fields; backend may not support these yet
  final String pathPattern;
  final String ruleType;
  final bool isActive;
  // Security fields
  final bool enableHsts;
  final int hstsMaxAge;
  final bool enableSecurityHeaders;
  final String? customHeaders;
  final String? rateLimit;
  final bool sslEnabled;
  final bool forceHttps;
  final int createdBy;
  final DateTime createdAt;
  final DateTime updatedAt;

  ProxyRule({
    required this.id,
    required this.domain,
    required this.backendId,
    this.accessControl,
    this.ipWhitelist,
    required this.pathPattern,
    required this.ruleType,
    required this.isActive,
    this.enableHsts = false,
    this.hstsMaxAge = 31536000,
    this.enableSecurityHeaders = true,
    this.customHeaders,
    this.rateLimit,
    this.sslEnabled = true,
    this.forceHttps = true,
    required this.createdBy,
    required this.createdAt,
    required this.updatedAt,
  });

  factory ProxyRule.fromJson(Map<String, dynamic> json) {
    return ProxyRule(
      id: json['id'] as int? ?? 0,
      // Backend uses 'frontend_domain'
      domain: json['frontend_domain'] as String? ?? json['domain'] as String? ?? '',
      backendId: json['backend_id'] as int? ?? 0,
      accessControl: json['access_control'] as String?,
      ipWhitelist: json['ip_whitelist'] as String?,
      // Optional / not yet in backend – keep defaults if missing
      pathPattern: json['path_pattern'] as String? ?? '/',
      ruleType: json['rule_type'] as String? ?? 'reverse_proxy',
      isActive: json['is_active'] as bool? ?? true,
      // Security fields
      enableHsts: json['enable_hsts'] as bool? ?? false,
      hstsMaxAge: json['hsts_max_age'] as int? ?? 31536000,
      enableSecurityHeaders: json['enable_security_headers'] as bool? ?? true,
      customHeaders: json['custom_headers'] as String?,
      rateLimit: json['rate_limit'] as String?,
      sslEnabled: json['ssl_enabled'] as bool? ?? true,
      forceHttps: json['force_https'] as bool? ?? true,
      createdBy: json['created_by'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String? ?? DateTime.now().toIso8601String()),
      updatedAt: DateTime.parse(json['updated_at'] as String? ?? DateTime.now().toIso8601String()),
    );
  }

  Map<String, dynamic> toJson() => {
    // Backend expects 'frontend_domain'
    'frontend_domain': domain,
    'backend_id': backendId,
    if (accessControl != null) 'access_control': accessControl,
    if (ipWhitelist != null) 'ip_whitelist': ipWhitelist,
    // Include is_active for updates
    'is_active': isActive,
    // Security fields
    'enable_hsts': enableHsts,
    'hsts_max_age': hstsMaxAge,
    'enable_security_headers': enableSecurityHeaders,
    if (customHeaders != null) 'custom_headers': customHeaders,
    if (rateLimit != null) 'rate_limit': rateLimit,
    'ssl_enabled': sslEnabled,
    'force_https': forceHttps,
  };
}

/// SSL Certificate model
class Certificate {
  final int id;
  final String domain;
  final DateTime expiryDate;
  final bool isExpired;
  final int expiringInDays;
  final String description;
  final DateTime createdAt;
  final DateTime updatedAt;

  Certificate({
    required this.id,
    required this.domain,
    required this.expiryDate,
    required this.isExpired,
    required this.expiringInDays,
    required this.description,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Certificate.fromJson(Map<String, dynamic> json) {
    final expiry = DateTime.parse(json['expiry_date'] as String? ?? DateTime.now().toIso8601String());
    final now = DateTime.now();
    final expiringInDays = expiry.difference(now).inDays;

    return Certificate(
      id: json['id'] as int? ?? 0,
      domain: json['domain'] as String? ?? '',
      expiryDate: expiry,
      isExpired: expiringInDays < 0,
      expiringInDays: expiringInDays,
      description: json['description'] as String? ?? '',
      createdAt: DateTime.parse(json['created_at'] as String? ?? DateTime.now().toIso8601String()),
      updatedAt: DateTime.parse(json['updated_at'] as String? ?? DateTime.now().toIso8601String()),
    );
  }

  Map<String, dynamic> toJson() => {
    'domain': domain,
    'description': description,
  };

  String get expiryStatus {
    if (isExpired) return 'Expired';
    if (expiringInDays < 7) return 'Critical';
    if (expiringInDays < 30) return 'Warning';
    return 'Valid';
  }
}

/// Health Status model
class HealthStatus {
  final String status;
  final String version;
  final bool nginxHealthy;
  final bool databaseHealthy;
  final int activeBackends;
  final int activeRules;
  final int totalConnections;

  HealthStatus({
    required this.status,
    required this.version,
    required this.nginxHealthy,
    required this.databaseHealthy,
    required this.activeBackends,
    required this.activeRules,
    required this.totalConnections,
  });

  factory HealthStatus.fromJson(Map<String, dynamic> json) {
    return HealthStatus(
      status: json['status'] as String? ?? 'unknown',
      version: json['version'] as String? ?? '0.0.0',
      nginxHealthy: json['nginx_healthy'] as bool? ?? false,
      databaseHealthy: json['database_healthy'] as bool? ?? false,
      activeBackends: json['active_backends'] as int? ?? 0,
      activeRules: json['active_rules'] as int? ?? 0,
      totalConnections: json['total_connections'] as int? ?? 0,
    );
  }

  bool get isHealthy => status == 'healthy';
}

/// Metrics model
class Metrics {
  final DateTime timestamp;
  final int requestCount;
  final double averageResponseTime;
  final int errorCount;
  final Map<String, dynamic>? additionalData;

  Metrics({
    required this.timestamp,
    required this.requestCount,
    required this.averageResponseTime,
    required this.errorCount,
    this.additionalData,
  });

  factory Metrics.fromJson(Map<String, dynamic> json) {
    return Metrics(
      timestamp: DateTime.parse(json['timestamp'] as String? ?? DateTime.now().toIso8601String()),
      requestCount: json['request_count'] as int? ?? 0,
      averageResponseTime: (json['average_response_time'] as num?)?.toDouble() ?? 0.0,
      errorCount: json['error_count'] as int? ?? 0,
      additionalData: json['data'] as Map<String, dynamic>?,
    );
  }
}

/// API Response wrapper
class ApiResponse<T> {
  final bool success;
  final T? data;
  final String? message;
  final String? error;

  ApiResponse({
    required this.success,
    this.data,
    this.message,
    this.error,
  });

  factory ApiResponse.fromJson(Map<String, dynamic> json, T Function(dynamic) fromJson) {
    return ApiResponse(
      success: json['status'] == 'success',
      data: json['data'] != null ? fromJson(json['data']) : null,
      message: json['message'] as String?,
      error: json['error'] as String?,
    );
  }
}

/// Audit Log Entry model
class AuditLogEntry {
  final int id;
  final int userId;
  final String action;
  final String entityType;
  final int? entityId;
  final Map<String, dynamic> changes;
  final DateTime timestamp;

  AuditLogEntry({
    required this.id,
    required this.userId,
    required this.action,
    required this.entityType,
    this.entityId,
    required this.changes,
    required this.timestamp,
  });

  factory AuditLogEntry.fromJson(Map<String, dynamic> json) {
    return AuditLogEntry(
      id: json['id'] as int? ?? 0,
      userId: json['user_id'] as int? ?? 0,
      action: json['action'] as String? ?? '',
      entityType: json['entity_type'] as String? ?? '',
      entityId: json['entity_id'] as int?,
      changes: json['changes'] as Map<String, dynamic>? ?? {},
      timestamp: DateTime.parse(json['timestamp'] as String? ?? DateTime.now().toIso8601String()),
    );
  }
}
