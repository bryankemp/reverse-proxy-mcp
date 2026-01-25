import 'package:flutter/foundation.dart';
import '../models/models.dart';
import '../services/api_service.dart';

/// Provider for managing backend servers
class BackendProvider extends ChangeNotifier {
  final ApiService _apiService;

  List<BackendServer> _backends = [];
  bool _isLoading = false;
  String? _error;

  BackendProvider(this._apiService);

  // Getters
  List<BackendServer> get backends => _backends;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isEmpty => _backends.isEmpty;

  /// Fetch all backends
  Future<void> fetchBackends({int limit = 50, int offset = 0}) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      _backends = await _apiService.listBackends(limit: limit, offset: offset);
      notifyListeners();
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
    } catch (e) {
      _error = 'Failed to fetch backends: $e';
      notifyListeners();
    } finally {
      _isLoading = false;
    }
  }

  /// Get single backend
  Future<BackendServer?> getBackend(int id) async {
    try {
      return await _apiService.getBackend(id);
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return null;
    }
  }

  /// Create new backend
  Future<bool> createBackend({
    required String name,
    required String host,
    required int port,
    String protocol = 'http',
    String description = '',
  }) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final backend = await _apiService.createBackend(
        name: name,
        host: host,
        port: port,
        protocol: protocol,
        description: description,
      );

      _backends.add(backend);
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } catch (e) {
      _error = 'Failed to create backend: $e';
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
    }
  }

  /// Update backend
  Future<bool> updateBackend({
    required int id,
    required String name,
    required String host,
    required int port,
    String protocol = 'http',
    String description = '',
  }) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final backend = BackendServer(
        id: id,
        name: name,
        host: host,
        port: port,
        protocol: protocol,
        description: description,
        isActive: true,
        createdBy: 0,
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      final updated = await _apiService.updateBackend(id, backend);
      
      final index = _backends.indexWhere((b) => b.id == id);
      if (index >= 0) {
        _backends[index] = updated;
      }

      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } catch (e) {
      _error = 'Failed to update backend: $e';
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
    }
  }

  /// Delete backend
  Future<bool> deleteBackend(int id) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      await _apiService.deleteBackend(id);
      _backends.removeWhere((b) => b.id == id);

      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      notifyListeners();
      return false;
    } catch (e) {
      _error = 'Failed to delete backend: $e';
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
    }
  }

  /// Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
