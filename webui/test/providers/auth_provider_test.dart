import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:reverse_proxy_mcp_webui/providers/auth_provider.dart';
import 'package:reverse_proxy_mcp_webui/services/api_service.dart';
import 'package:reverse_proxy_mcp_webui/services/storage_service.dart';

import 'auth_provider_test.mocks.dart';

@GenerateMocks([ApiService, StorageService])
void main() {
  late MockApiService mockApiService;
  late MockStorageService mockStorage;
  late AuthProvider authProvider;

  setUp(() {
    mockApiService = MockApiService();
    mockStorage = MockStorageService();
    authProvider = AuthProvider(mockApiService, mockStorage);
  });

  group('AuthProvider - Login', () {
    test('successful login updates state correctly', () async {
      // Arrange
      const email = 'admin@test.com';
      const password = 'password123';
      const token = 'fake-jwt-token';
      
      when(mockApiService.login(email: email, password: password))
          .thenAnswer((_) async => {
                'access_token': token,
                'token_type': 'bearer',
                'expires_in': 86400,
                'user': {
                  'id': 1,
                  'username': 'admin',
                  'email': email,
                  'role': 'admin',
                  'is_active': true,
                  'created_at': '2024-01-01T00:00:00Z',
                  'updated_at': '2024-01-01T00:00:00Z',
                }
              });
      
      when(mockApiService.setToken(token)).thenAnswer((_) async => {});
      when(mockStorage.saveToken(token)).thenAnswer((_) async => {});
      when(mockStorage.saveRememberMe(false)).thenAnswer((_) async => {});

      // Act
      final result = await authProvider.login(email: email, password: password);

      // Assert
      expect(result, true);
      expect(authProvider.isLoggedIn, true);
      expect(authProvider.token, token);
      expect(authProvider.currentUser?.email, email);
      expect(authProvider.isAdmin, true);
      expect(authProvider.error, null);
    });

    test('failed login sets error state', () async {
      // Arrange
      when(mockApiService.login(email: anyNamed('email'), password: anyNamed('password')))
          .thenThrow(ApiException(message: 'Invalid credentials', statusCode: 401));

      // Act
      final result = await authProvider.login(
        email: 'wrong@test.com',
        password: 'wrongpass',
      );

      // Assert
      expect(result, false);
      expect(authProvider.isLoggedIn, false);
      expect(authProvider.token, null);
      expect(authProvider.error, 'Invalid credentials');
    });

    test('login with remember me saves email', () async {
      // Arrange
      const email = 'admin@test.com';
      const password = 'password123';
      const token = 'fake-token';
      
      when(mockApiService.login(email: email, password: password))
          .thenAnswer((_) async => {
                'access_token': token,
                'token_type': 'bearer',
                'expires_in': 86400,
              });
      
      when(mockApiService.setToken(any)).thenAnswer((_) async => {});
      when(mockStorage.saveToken(any)).thenAnswer((_) async => {});
      when(mockStorage.saveRememberMe(true)).thenAnswer((_) async => {});
      when(mockStorage.saveEmail(email)).thenAnswer((_) async => {});

      // Act
      await authProvider.login(
        email: email,
        password: password,
        rememberMe: true,
      );

      // Assert
      verify(mockStorage.saveRememberMe(true)).called(1);
      verify(mockStorage.saveEmail(email)).called(1);
    });
  });

  group('AuthProvider - Logout', () {
    test('logout clears all state', () async {
      // Arrange
      when(mockApiService.logout()).thenAnswer((_) async => {});
      when(mockStorage.deleteToken()).thenAnswer((_) async => {});
      when(mockApiService.clearAuth()).thenAnswer((_) async => {});

      // Act
      await authProvider.logout();

      // Assert
      expect(authProvider.isLoggedIn, false);
      expect(authProvider.token, null);
      expect(authProvider.currentUser, null);
      verify(mockStorage.deleteToken()).called(1);
      verify(mockApiService.clearAuth()).called(1);
    });
  });

  group('AuthProvider - Initialize', () {
    test('initialize with stored token sets logged in state', () async {
      // Arrange
      const token = 'stored-token';
      when(mockStorage.getToken()).thenAnswer((_) async => token);
      when(mockApiService.setToken(token)).thenAnswer((_) async => {});

      // Act
      await authProvider.initializeStoredAuth();

      // Assert
      expect(authProvider.isLoggedIn, true);
      expect(authProvider.token, token);
    });

    test('initialize without stored token sets logged out state', () async {
      // Arrange
      when(mockStorage.getToken()).thenAnswer((_) async => null);

      // Act
      await authProvider.initializeStoredAuth();

      // Assert
      expect(authProvider.isLoggedIn, false);
      expect(authProvider.token, null);
    });
  });
}
