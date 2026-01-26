import 'package:flutter/foundation.dart';
import '../models/models.dart';
import '../services/api_service.dart';

/// Provider for managing proxy rules
class RuleProvider extends ChangeNotifier {
  final ApiService _apiService;
  List<ProxyRule> _rules = [];
  bool _isLoading = false;
  bool _isReloading = false;
  String? _error;

  RuleProvider(this._apiService);

  List<ProxyRule> get rules => _rules;
  bool get isLoading => _isLoading;
  bool get isReloading => _isReloading;
  String? get error => _error;

  Future<void> fetchRules({int limit = 50, int offset = 0}) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();
      _rules = await _apiService.listProxyRules(limit: limit, offset: offset);
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
    } catch (e) {
      _error = 'Failed to fetch rules: $e';
      notifyListeners();
    } finally {
      _isLoading = false;
    }
  }

  Future<bool> createRule({
    required String domain,
    required int backendId,
    String pathPattern = '/',
    String ruleType = 'reverse_proxy',
    bool enableHsts = false,
    bool forceHttps = true,
    bool sslEnabled = true,
    String? rateLimit,
    String? ipWhitelist,
  }) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final rule = await _apiService.createProxyRule(
        domain: domain,
        backendId: backendId,
        pathPattern: pathPattern,
        ruleType: ruleType,
        enableHsts: enableHsts,
        forceHttps: forceHttps,
        sslEnabled: sslEnabled,
        rateLimit: rateLimit,
        ipWhitelist: ipWhitelist,
      );
      _rules.add(rule);
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
    }
  }

  Future<bool> updateRule({
    required int id,
    required String domain,
    required int backendId,
    String pathPattern = '/',
    String ruleType = 'reverse_proxy',
    bool? isActive,
    bool? enableHsts,
    bool? forceHttps,
    bool? sslEnabled,
    String? rateLimit,
    String? ipWhitelist,
  }) async {
    try {
      _isLoading = true;
      // Get existing rule to preserve fields not being updated
      final existing = _rules.firstWhere((r) => r.id == id);
      final rule = ProxyRule(
        id: id,
        domain: domain,
        backendId: backendId,
        pathPattern: pathPattern,
        ruleType: ruleType,
        isActive: isActive ?? existing.isActive,
        createdBy: existing.createdBy,
        createdAt: existing.createdAt,
        updatedAt: DateTime.now(),
        enableHsts: enableHsts ?? existing.enableHsts,
        forceHttps: forceHttps ?? existing.forceHttps,
        sslEnabled: sslEnabled ?? existing.sslEnabled,
        rateLimit: rateLimit ?? existing.rateLimit,
        ipWhitelist: ipWhitelist ?? existing.ipWhitelist,
      );
      final updated = await _apiService.updateProxyRule(id, rule);
      final index = _rules.indexWhere((r) => r.id == id);
      if (index >= 0) _rules[index] = updated;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
    }
  }

  Future<bool> deleteRule(int id) async {
    try {
      _isLoading = true;
      await _apiService.deleteProxyRule(id);
      _rules.removeWhere((r) => r.id == id);
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
    }
  }

  Future<bool> reloadNginx() async {
    try {
      _isReloading = true;
      _error = null;
      notifyListeners();
      await _apiService.reloadNginx();
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } finally {
      _isReloading = false;
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}

/// Provider for managing SSL certificates
class CertificateProvider extends ChangeNotifier {
  final ApiService _apiService;
  List<Certificate> _certificates = [];
  bool _isLoading = false;
  String? _error;

  CertificateProvider(this._apiService);

  List<Certificate> get certificates => _certificates;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchCertificates({int limit = 50, int offset = 0}) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();
      _certificates = await _apiService.listCertificates(limit: limit, offset: offset);
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
    } catch (e) {
      _error = 'Failed to fetch certificates: $e';
      notifyListeners();
    } finally {
      _isLoading = false;
    }
  }

  Future<bool> createCertificate({
    required String name,
    required String domain,
    required String certificate,
    required String privateKey,
  }) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();
      // API call would go here - for now just add locally
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
    }
  }

  Future<bool> deleteCertificate(int id) async {
    try {
      _isLoading = true;
      await _apiService.deleteCertificate(id);
      _certificates.removeWhere((c) => c.id == id);
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
    }
  }

  List<Certificate> getExpiringCertificates(int daysThreshold) {
    return _certificates.where((c) => c.expiringInDays <= daysThreshold).toList();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}

/// Provider for system metrics
class MetricsProvider extends ChangeNotifier {
  final ApiService _apiService;
  List<Metrics> _metrics = [];
  bool _isLoading = false;
  String? _error;

  MetricsProvider(this._apiService);

  List<Metrics> get metrics => _metrics;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchMetrics({String metricType = 'requests', int limit = 100}) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();
      _metrics = await _apiService.getMetrics(metricType: metricType, limit: limit);
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
    } catch (e) {
      _error = 'Failed to fetch metrics: $e';
      notifyListeners();
    } finally {
      _isLoading = false;
    }
  }

  int getTotalRequests() {
    return _metrics.fold(0, (sum, m) => sum + m.requestCount);
  }

  double getAverageResponseTime() {
    if (_metrics.isEmpty) return 0;
    final sum = _metrics.fold(0.0, (total, m) => total + m.averageResponseTime);
    return sum / _metrics.length;
  }

  int getTotalErrors() {
    return _metrics.fold(0, (sum, m) => sum + m.errorCount);
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
