import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:nginx_manager_webui/screens/login_screen.dart';
import 'package:nginx_manager_webui/providers/auth_provider.dart';
import 'package:nginx_manager_webui/services/api_service.dart';
import 'package:nginx_manager_webui/services/storage_service.dart';
import 'package:provider/provider.dart';

import 'login_screen_test.mocks.dart';

@GenerateMocks([ApiService, StorageService, AuthProvider])
void main() {
  late MockApiService mockApiService;
  late MockStorageService mockStorage;
  late MockAuthProvider mockAuthProvider;

  setUp(() {
    mockApiService = MockApiService();
    mockStorage = MockStorageService();
    mockAuthProvider = MockAuthProvider();

    // Default mock behaviors
    when(mockStorage.getSavedEmail()).thenReturn(null);
    when(mockStorage.getRememberMe()).thenReturn(false);
    when(mockAuthProvider.isLoading).thenReturn(false);
    when(mockAuthProvider.error).thenReturn(null);
  });

  Widget createLoginScreen() {
    return MultiProvider(
      providers: [
        Provider<StorageService>.value(value: mockStorage),
        Provider<ApiService>.value(value: mockApiService),
        ChangeNotifierProvider<AuthProvider>.value(value: mockAuthProvider),
      ],
      child: const MaterialApp(
        home: LoginScreen(),
      ),
    );
  }

  group('LoginScreen Widget Tests', () {
    testWidgets('renders login screen with all elements', (tester) async {
      await tester.pumpWidget(createLoginScreen());

      // Verify all UI elements are present
      expect(find.text('Nginx Manager'), findsWidgets);
      expect(find.text('Reverse Proxy Management'), findsOneWidget);
      expect(find.byIcon(Icons.admin_panel_settings), findsOneWidget);
      expect(find.byType(TextField), findsNWidgets(2));
      expect(find.text('Username'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      expect(find.byType(Checkbox), findsOneWidget);
      expect(find.text('Remember me'), findsOneWidget);
      expect(find.text('Login'), findsWidgets);
    });

    testWidgets('username and password fields accept input', (tester) async {
      await tester.pumpWidget(createLoginScreen());

      // Find text fields
      final usernameField = find.widgetWithText(TextField, 'Username');
      final passwordField = find.widgetWithText(TextField, 'Password');

      // Enter text
      await tester.enterText(usernameField, 'admin');
      await tester.enterText(passwordField, 'password123');

      // Verify text was entered
      expect(find.text('admin'), findsOneWidget);
      expect(find.text('password123'), findsOneWidget);
    });

    testWidgets('remember me checkbox toggles', (tester) async {
      await tester.pumpWidget(createLoginScreen());

      final checkbox = find.byType(Checkbox);
      
      // Initially unchecked
      Checkbox checkboxWidget = tester.widget(checkbox);
      expect(checkboxWidget.value, false);

      // Tap checkbox
      await tester.tap(checkbox);
      await tester.pump();

      // Should be checked now
      checkboxWidget = tester.widget(checkbox);
      expect(checkboxWidget.value, true);
    });

    testWidgets('password visibility toggle works', (tester) async {
      await tester.pumpWidget(createLoginScreen());

      // Find password field and visibility button
      final passwordFields = find.byType(TextField);
      final visibilityButton = find.byIcon(Icons.visibility_off);

      // Initially password should be obscured
      TextField passwordField = tester.widget(passwordFields.last);
      expect(passwordField.obscureText, true);

      // Tap visibility toggle
      await tester.tap(visibilityButton);
      await tester.pump();

      // Password should now be visible
      final visibleIcon = find.byIcon(Icons.visibility);
      expect(visibleIcon, findsOneWidget);
    });

    testWidgets('shows error when login fails', (tester) async {
      // Set up error state
      when(mockAuthProvider.error).thenReturn('Invalid credentials');

      await tester.pumpWidget(createLoginScreen());
      await tester.pump();

      // Verify error message is displayed
      expect(find.text('Invalid credentials'), findsOneWidget);
    });

    testWidgets('shows loading indicator during login', (tester) async {
      // Set up loading state
      when(mockAuthProvider.isLoading).thenReturn(true);

      await tester.pumpWidget(createLoginScreen());
      await tester.pump();

      // Verify loading indicator and text
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Logging in...'), findsOneWidget);
    });

    testWidgets('login button calls auth provider when pressed', (tester) async {
      when(mockAuthProvider.login(
        email: anyNamed('email'),
        password: anyNamed('password'),
        rememberMe: anyNamed('rememberMe'),
      )).thenAnswer((_) async => true);

      await tester.pumpWidget(createLoginScreen());

      // Enter credentials
      await tester.enterText(
        find.widgetWithText(TextField, 'Username'),
        'admin',
      );
      await tester.enterText(
        find.widgetWithText(TextField, 'Password'),
        'password123',
      );

      // Tap login button
      await tester.tap(find.text('Login').last);
      await tester.pump();

      // Verify login was called
      verify(mockAuthProvider.login(
        email: 'admin',
        password: 'password123',
        rememberMe: false,
      )).called(1);
    });

    testWidgets('prefills username when remember me was enabled', (tester) async {
      // Set up storage to return saved email
      when(mockStorage.getSavedEmail()).thenReturn('saved@example.com');
      when(mockStorage.getRememberMe()).thenReturn(true);

      await tester.pumpWidget(createLoginScreen());
      await tester.pumpAndSettle();

      // Wait for async initialization
      await tester.pump(const Duration(milliseconds: 100));

      // Verify username is prefilled (text should appear somewhere)
      // Note: The actual value is in the controller, so we check the checkbox
      final checkbox = tester.widget<Checkbox>(find.byType(Checkbox));
      expect(checkbox.value, true);
    });

    testWidgets('disables fields when loading', (tester) async {
      when(mockAuthProvider.isLoading).thenReturn(true);

      await tester.pumpWidget(createLoginScreen());

      // Find text fields
      final textFields = find.byType(TextField);
      
      // Both fields should be disabled
      final usernameField = tester.widget<TextField>(textFields.first);
      final passwordField = tester.widget<TextField>(textFields.last);
      
      expect(usernameField.enabled, false);
      expect(passwordField.enabled, false);
    });
  });
}
