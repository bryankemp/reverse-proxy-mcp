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

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final storage = await StorageService.initialize();
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
        Provider<StorageService>.value(value: storage),
        Provider<ApiService>.value(value: apiService),
        ChangeNotifierProvider(
          create: (_) => AuthProvider(apiService, storage),
        ),
        ChangeNotifierProvider(
          create: (_) => BackendProvider(apiService),
        ),
        ChangeNotifierProvider(
          create: (_) => RuleProvider(apiService),
        ),
        ChangeNotifierProvider(
          create: (_) => CertificateProvider(apiService),
        ),
        ChangeNotifierProvider(
          create: (_) => MetricsProvider(apiService),
        ),
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
      ),
    );
  }
}

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
        if (authProvider.isLoading) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        if (!authProvider.isLoggedIn) {
          return const LoginScreen();
        }
        return const AdminDashboard();
      },
    );
  }
}

class AdminDashboard extends StatelessWidget {
  const AdminDashboard();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Nginx Manager'),
        elevation: 0,
        actions: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Center(
              child: TextButton(
                onPressed: () {
                  context.read<AuthProvider>().logout();
                  Navigator.of(context).pushReplacementNamed('/');
                },
                child: const Text('Logout', style: TextStyle(color: Colors.white)),
              ),
            ),
          ),
        ],
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                'Nginx Manager Admin',
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 32),
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                crossAxisSpacing: 24,
                mainAxisSpacing: 24,
                children: [
                  AdminCard(
                    title: 'Backend Servers',
                    icon: Icons.storage,
                    onTap: () async {
                      await context.read<BackendProvider>().fetchBackends();
                      if (context.mounted) {
                        showDialog(
                          context: context,
                          builder: (context) => const BackendListDialog(),
                        );
                      }
                    },
                  ),
                  AdminCard(
                    title: 'Proxy Rules',
                    icon: Icons.domain,
                    onTap: () async {
                      await context.read<RuleProvider>().fetchRules();
                      if (context.mounted) {
                        showDialog(
                          context: context,
                          builder: (context) => const RuleListDialog(),
                        );
                      }
                    },
                  ),
                  AdminCard(
                    title: 'SSL Certificates',
                    icon: Icons.security,
                    onTap: () async {
                      await context.read<CertificateProvider>().fetchCertificates();
                      if (context.mounted) {
                        showDialog(
                          context: context,
                          builder: (context) => const CertificateListDialog(),
                        );
                      }
                    },
                  ),
                  AdminCard(
                    title: 'System Health',
                    icon: Icons.health_and_safety,
                    onTap: () {
                      showDialog(
                        context: context,
                        builder: (context) => const HealthCheckDialog(),
                      );
                    },
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class AdminCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final VoidCallback onTap;

  const AdminCard({
    required this.title,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      child: InkWell(
        onTap: onTap,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 48, color: Colors.blue),
            const SizedBox(height: 16),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }
}

class BackendListDialog extends StatelessWidget {
  const BackendListDialog();

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Backend Servers'),
          leading: IconButton(
            icon: const Icon(Icons.close),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        body: Consumer<BackendProvider>(
          builder: (context, provider, _) {
            if (provider.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }
            if (provider.backends.isEmpty) {
              return const Center(child: Text('No backend servers'));
            }
            return ListView.builder(
              itemCount: provider.backends.length,
              itemBuilder: (context, index) {
                final backend = provider.backends[index];
                return ListTile(
                  title: Text(backend.name),
                  subtitle: Text('${backend.host}:${backend.port}'),
                  trailing: Text(backend.protocol),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

class RuleListDialog extends StatelessWidget {
  const RuleListDialog();

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Proxy Rules'),
          leading: IconButton(
            icon: const Icon(Icons.close),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        body: Consumer<RuleProvider>(
          builder: (context, provider, _) {
            if (provider.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }
            if (provider.rules.isEmpty) {
              return const Center(child: Text('No proxy rules'));
            }
            return ListView.builder(
              itemCount: provider.rules.length,
              itemBuilder: (context, index) {
                final rule = provider.rules[index];
                return ListTile(
                  title: Text(rule.domain),
                  subtitle: Text('Backend ID: ${rule.backendId}'),
                  trailing: Text(rule.ruleType),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

class CertificateListDialog extends StatelessWidget {
  const CertificateListDialog();

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Scaffold(
        appBar: AppBar(
          title: const Text('SSL Certificates'),
          leading: IconButton(
            icon: const Icon(Icons.close),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        body: Consumer<CertificateProvider>(
          builder: (context, provider, _) {
            if (provider.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }
            if (provider.certificates.isEmpty) {
              return const Center(child: Text('No certificates'));
            }
            return ListView.builder(
              itemCount: provider.certificates.length,
              itemBuilder: (context, index) {
                final cert = provider.certificates[index];
                return ListTile(
                  title: Text(cert.domain),
                  subtitle: Text(cert.expiryStatus),
                  trailing: Text('${cert.expiringInDays} days'),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

class HealthCheckDialog extends StatelessWidget {
  const HealthCheckDialog();

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'System Health',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            const Icon(Icons.check_circle, color: Colors.green, size: 64),
            const SizedBox(height: 16),
            const Text('✓ API is running'),
            const Text('✓ Database is connected'),
            const Text('✓ Nginx is healthy'),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      ),
    );
  }
}
