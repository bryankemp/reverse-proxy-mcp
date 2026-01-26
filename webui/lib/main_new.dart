import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'config/app_config.dart';
import 'providers/auth_provider.dart';
import 'providers/backend_provider.dart';
import 'providers/other_providers.dart';
import 'services/api_service.dart';
import 'services/storage_service.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/backends_screen.dart';
import 'screens/rules_screen.dart';
import 'screens/certificates_screen.dart';
import 'screens/users_screen.dart';
import 'screens/audit_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize storage service
  final storage = await StorageService.initialize();

  // Create API service
  final apiService = ApiService(storage);

  runApp(MyApp(storage: storage, apiService: apiService));
}

class MyApp extends StatelessWidget {
  final StorageService storage;
  final ApiService apiService;

  const MyApp({required this.storage, required this.apiService});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // Core services
        Provider<StorageService>.value(value: storage),
        Provider<ApiService>.value(value: apiService),

        // Auth provider (CRITICAL - must be first)
        ChangeNotifierProvider(
          create: (_) => AuthProvider(apiService, storage),
        ),

        // Data providers
        ChangeNotifierProvider(create: (_) => BackendProvider(apiService)),
        ChangeNotifierProvider(create: (_) => RuleProvider(apiService)),
        ChangeNotifierProvider(create: (_) => CertificateProvider(apiService)),
        ChangeNotifierProvider(create: (_) => MetricsProvider(apiService)),
      ],
      child: MaterialApp(
        title: AppConfig.appName,
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.blue,
            brightness: Brightness.light,
          ),
          textTheme: GoogleFonts.robotoTextTheme(),
          appBarTheme: AppBarTheme(
            centerTitle: true,
            elevation: 2,
            backgroundColor: Colors.blue,
            foregroundColor: Colors.white,
            titleTextStyle: GoogleFonts.roboto(
              fontSize: 20,
              fontWeight: FontWeight.w600,
              color: Colors.white,
            ),
          ),
        ),
        home: const AppRouter(),
        routes: {
          '/login': (context) => const LoginScreen(),
          '/dashboard': (context) => const DashboardScreen(),
          '/backends': (context) => const BackendsScreen(),
          '/rules': (context) => const RulesScreen(),
          '/certificates': (context) => const CertificatesScreen(),
          '/users': (context) => const UsersScreen(),
          '/audit': (context) => const AuditScreen(),
        },
      ),
    );
  }
}

/// Router widget that handles navigation based on auth state
class AppRouter extends StatefulWidget {
  const AppRouter();

  @override
  State<AppRouter> createState() => _AppRouterState();
}

class _AppRouterState extends State<AppRouter> {
  bool _initialized = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();

    if (!_initialized) {
      _initialized = true;
      // Initialize auth on first build
      WidgetsBinding.instance.addPostFrameCallback((_) {
        final auth = Provider.of<AuthProvider>(context, listen: false);
        if (!auth.isLoggedIn) {
          auth.initializeStoredAuth();
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, _) {
        // Show loading while initializing
        if (authProvider.isLoading) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        // Show login if not authenticated
        if (!authProvider.isLoggedIn) {
          return const LoginScreen();
        }

        // Show dashboard if authenticated
        return const DashboardScreen();
      },
    );
  }
}
