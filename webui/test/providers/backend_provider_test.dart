import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:reverse_proxy_mcp_webui/providers/backend_provider.dart';
import 'package:reverse_proxy_mcp_webui/services/api_service.dart';
import 'package:reverse_proxy_mcp_webui/models/models.dart';

import 'backend_provider_test.mocks.dart';

@GenerateMocks([ApiService])
void main() {
  late MockApiService mockApiService;
  late BackendProvider backendProvider;

  setUp(() {
    mockApiService = MockApiService();
    backendProvider = BackendProvider(mockApiService);
  });

  group('BackendProvider - Fetch', () {
    test('fetchBackends successfully loads backends', () async {
      // Arrange
      final mockBackends = [
        BackendServer(
          id: 1,
          name: 'Backend 1',
          host: '192.168.1.10',
          port: 8080,
          protocol: 'http',
          description: 'Test backend',
          isActive: true,
          createdBy: 1,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        BackendServer(
          id: 2,
          name: 'Backend 2',
          host: '192.168.1.20',
          port: 9090,
          protocol: 'https',
          description: 'Another test backend',
          isActive: true,
          createdBy: 1,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
      ];

      when(mockApiService.listBackends(limit: anyNamed('limit'), offset: anyNamed('offset')))
          .thenAnswer((_) async => mockBackends);

      // Act
      await backendProvider.fetchBackends();

      // Assert
      expect(backendProvider.backends.length, 2);
      expect(backendProvider.backends[0].name, 'Backend 1');
      expect(backendProvider.backends[1].name, 'Backend 2');
      expect(backendProvider.error, null);
      expect(backendProvider.isEmpty, false);
    });

    test('fetchBackends handles API error', () async {
      // Arrange
      when(mockApiService.listBackends(limit: anyNamed('limit'), offset: anyNamed('offset')))
          .thenThrow(ApiException(message: 'Failed to load backends', statusCode: 500));

      // Act
      await backendProvider.fetchBackends();

      // Assert
      expect(backendProvider.backends.length, 0);
      expect(backendProvider.error, 'Failed to load backends');
      expect(backendProvider.isEmpty, true);
    });
  });

  group('BackendProvider - Create', () {
    test('createBackend adds new backend to list', () async {
      // Arrange
      final newBackend = BackendServer(
        id: 3,
        name: 'New Backend',
        host: '192.168.1.30',
        port: 3000,
        protocol: 'http',
        description: 'Newly created',
        isActive: true,
        createdBy: 1,
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      when(mockApiService.createBackend(
        name: anyNamed('name'),
        host: anyNamed('host'),
        port: anyNamed('port'),
        protocol: anyNamed('protocol'),
        description: anyNamed('description'),
      )).thenAnswer((_) async => newBackend);

      // Act
      final result = await backendProvider.createBackend(
        name: 'New Backend',
        host: '192.168.1.30',
        port: 3000,
        description: 'Newly created',
      );

      // Assert
      expect(result, true);
      expect(backendProvider.backends.length, 1);
      expect(backendProvider.backends[0].name, 'New Backend');
      expect(backendProvider.error, null);
    });

    test('createBackend handles error', () async {
      // Arrange
      when(mockApiService.createBackend(
        name: anyNamed('name'),
        host: anyNamed('host'),
        port: anyNamed('port'),
        protocol: anyNamed('protocol'),
        description: anyNamed('description'),
      )).thenThrow(ApiException(message: 'Name already exists', statusCode: 409));

      // Act
      final result = await backendProvider.createBackend(
        name: 'Duplicate',
        host: '192.168.1.40',
        port: 4000,
      );

      // Assert
      expect(result, false);
      expect(backendProvider.error, 'Name already exists');
    });
  });

  group('BackendProvider - Delete', () {
    test('deleteBackend removes backend from list', () async {
      // Arrange
      final backend = BackendServer(
        id: 1,
        name: 'To Delete',
        host: '192.168.1.50',
        port: 5000,
        protocol: 'http',
        description: '',
        isActive: true,
        createdBy: 1,
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      backendProvider.backends.add(backend);
      when(mockApiService.deleteBackend(1)).thenAnswer((_) async => {});

      // Act
      final result = await backendProvider.deleteBackend(1);

      // Assert
      expect(result, true);
      expect(backendProvider.backends.length, 0);
      expect(backendProvider.error, null);
    });
  });

  group('BackendProvider - Error Handling', () {
    test('clearError resets error state', () {
      // Arrange
      backendProvider.backends.clear();

      // Act
      backendProvider.clearError();

      // Assert
      expect(backendProvider.error, null);
    });
  });
}
