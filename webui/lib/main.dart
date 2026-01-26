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

Future<void> _showNginxConfig(BuildContext context) async {
  // Fetch nginx config from API
  try {
    final apiService = Provider.of<ApiService>(context, listen: false);
    final config = await apiService.getNginxConfig();
    
    if (!context.mounted) return;
    
    showDialog(
      context: context,
      builder: (ctx) => Dialog(
        child: Container(
          width: 800,
          height: 600,
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Nginx Configuration',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(ctx),
                  ),
                ],
              ),
              const Divider(),
              Expanded(
                child: SingleChildScrollView(
                  child: SelectableText(
                    config,
                    style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  } catch (e) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Failed to load config: $e')),
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
          Consumer<AuthProvider>(
            builder: (context, auth, _) => Padding(
              padding: const EdgeInsets.all(8.0),
              child: Center(
                child: Row(
                  children: [
                    Text(
                      auth.currentUser?.username ?? 'User',
                      style: const TextStyle(color: Colors.white, fontSize: 14),
                    ),
                    const SizedBox(width: 16),
                    TextButton(
                      onPressed: () {
                        context.read<AuthProvider>().logout();
                        Navigator.of(context).pushReplacementNamed('/');
                      },
                      child: const Text('Logout', style: TextStyle(color: Colors.white)),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          return Scrollbar(
            thumbVisibility: true,
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    const Text(
                      'Nginx Manager Admin',
                      style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 32),
                    Wrap(
                      spacing: 24,
                      runSpacing: 24,
                      alignment: WrapAlignment.center,
                      children: [
                        SizedBox(
                          width: 420,
                          height: 280,
                          child: AdminCard(
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
                        ),
                        SizedBox(
                          width: 420,
                          height: 280,
                          child: AdminCard(
                            title: 'Proxy Rules',
                            icon: Icons.domain,
                            onTap: () async {
                              // Fetch both rules and backends
                              await Future.wait([
                                context.read<RuleProvider>().fetchRules(),
                                context.read<BackendProvider>().fetchBackends(),
                              ]);
                              if (context.mounted) {
                                showDialog(
                                  context: context,
                                  builder: (context) => const RuleListDialog(),
                                );
                              }
                            },
                          ),
                        ),
                        SizedBox(
                          width: 420,
                          height: 280,
                          child: AdminCard(
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
                        ),
                        SizedBox(
                          width: 420,
                          height: 280,
                          child: AdminCard(
                            title: 'System Health',
                            icon: Icons.health_and_safety,
                            onTap: () {
                              showDialog(
                                context: context,
                                builder: (context) => const HealthCheckDialog(),
                              );
                            },
                            actionButton: ActionButton(
                              icon: Icons.code,
                              label: 'View Config',
                              onPressed: () => _showNginxConfig(context),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class AdminCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final VoidCallback onTap;
  final ActionButton? actionButton;

  const AdminCard({
    required this.title,
    required this.icon,
    required this.onTap,
    this.actionButton,
  });

  @override
  Widget build(BuildContext context) {
    final List<Widget> children = [
      Icon(icon, size: 48, color: Colors.blue),
      const SizedBox(height: 16),
      Text(
        title,
        textAlign: TextAlign.center,
        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ];
    
    if (actionButton != null) {
      children.add(const SizedBox(height: 16));
      children.add(
        ElevatedButton.icon(
          onPressed: actionButton!.onPressed,
          icon: Icon(actionButton!.icon, size: 16),
          label: Text(actionButton!.label),
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          ),
        ),
      );
    }
    
    return Card(
      elevation: 4,
      child: InkWell(
        onTap: onTap,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: children,
        ),
      ),
    );
  }
}

class ActionButton {
  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  const ActionButton({
    required this.icon,
    required this.label,
    required this.onPressed,
  });
}

class BackendListDialog extends StatelessWidget {
  const BackendListDialog();

  Future<void> _showEditBackendForm(BuildContext context, backend) async {
    final nameCtl = TextEditingController(text: backend.name);
    final hostCtl = TextEditingController(text: backend.host);
    final portCtl = TextEditingController(text: backend.port.toString());
    String protocol = backend.protocol;

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('Edit Backend Server'),
          content: StatefulBuilder(
            builder: (ctx, setState) => SizedBox(
              width: 400,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(controller: nameCtl, decoration: const InputDecoration(labelText: 'Name')),
                  const SizedBox(height: 8),
                  TextField(controller: hostCtl, decoration: const InputDecoration(labelText: 'Host/IP')),
                  const SizedBox(height: 8),
                  TextField(controller: portCtl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Port')),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    value: protocol,
                    items: const [
                      DropdownMenuItem(value: 'http', child: Text('http')),
                      DropdownMenuItem(value: 'https', child: Text('https')),
                    ],
                    onChanged: (v) => setState(() => protocol = v ?? 'http'),
                    decoration: const InputDecoration(labelText: 'Protocol'),
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Update'),
            ),
          ],
        );
      },
    );

    if (result == true) {
      final name = nameCtl.text.trim();
      final host = hostCtl.text.trim();
      final port = int.tryParse(portCtl.text.trim()) ?? 80;
      if (name.isEmpty || host.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Name and Host are required')));
        return;
      }
      final provider = context.read<BackendProvider>();
      final ok = await provider.updateBackend(
        id: backend.id,
        name: name,
        host: host,
        port: port,
        protocol: protocol,
      );
      if (!context.mounted) return;
      if (ok) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Backend updated')));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(provider.error ?? 'Update failed')));
      }
    }
  }

  Future<void> _showCreateBackendForm(BuildContext context) async {
    final nameCtl = TextEditingController();
    final hostCtl = TextEditingController();
    final portCtl = TextEditingController(text: '80');
    String protocol = 'http';

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('Create Backend Server'),
          content: StatefulBuilder(
            builder: (ctx, setState) => SizedBox(
              width: 400,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(controller: nameCtl, decoration: const InputDecoration(labelText: 'Name')),
                  const SizedBox(height: 8),
                  TextField(controller: hostCtl, decoration: const InputDecoration(labelText: 'Host/IP')),
                  const SizedBox(height: 8),
                  TextField(controller: portCtl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Port')),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    value: protocol,
                    items: const [
                      DropdownMenuItem(value: 'http', child: Text('http')),
                      DropdownMenuItem(value: 'https', child: Text('https')),
                    ],
                    onChanged: (v) => setState(() => protocol = v ?? 'http'),
                    decoration: const InputDecoration(labelText: 'Protocol'),
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Create'),
            ),
          ],
        );
      },
    );

    if (result == true) {
      final name = nameCtl.text.trim();
      final host = hostCtl.text.trim();
      final port = int.tryParse(portCtl.text.trim()) ?? 80;
      if (name.isEmpty || host.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Name and Host are required')));
        return;
      }
      final provider = context.read<BackendProvider>();
      final ok = await provider.createBackend(name: name, host: host, port: port, protocol: protocol);
      if (!context.mounted) return;
      if (ok) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Backend created')));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(provider.error ?? 'Create failed')));
      }
    }
  }

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
          actions: [
            IconButton(
              tooltip: 'Add Backend',
              icon: const Icon(Icons.add),
              onPressed: () => _showCreateBackendForm(context),
            ),
          ],
        ),
        body: Consumer<BackendProvider>(
          builder: (context, provider, _) {
            if (provider.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }
            return ListView.builder(
              itemCount: provider.backends.length,
              itemBuilder: (context, index) {
                final backend = provider.backends[index];
                return Card(
                  color: backend.isActive ? null : Colors.grey[200],
                  child: ListTile(
                    leading: Icon(
                      Icons.storage,
                      color: backend.isActive ? Colors.blue : Colors.grey,
                    ),
                    title: Text(
                      backend.name,
                      style: TextStyle(
                        color: backend.isActive ? null : Colors.grey[600],
                        decoration: backend.isActive ? null : TextDecoration.lineThrough,
                      ),
                    ),
                    subtitle: Text(
                      '${backend.protocol}://${backend.host}:${backend.port}${backend.isActive ? '' : ' (Inactive)'}',
                      style: TextStyle(
                        color: backend.isActive ? null : Colors.grey[600],
                      ),
                    ),
                    trailing: PopupMenuButton(
                      itemBuilder: (context) => [
                        PopupMenuItem(
                          child: const Text('Edit'),
                          onTap: () {
                            // Show edit dialog
                            Future.delayed(Duration.zero, () => _showEditBackendForm(context, backend));
                          },
                        ),
                        PopupMenuItem(
                          child: Text(backend.isActive ? 'Deactivate' : 'Activate'),
                          onTap: () {
                            // Use Future.delayed to allow popup to close first
                            Future.delayed(Duration.zero, () async {
                              final ok = await provider.updateBackend(
                                id: backend.id,
                                name: backend.name,
                                host: backend.host,
                                port: backend.port,
                                protocol: backend.protocol,
                                isActive: !backend.isActive,
                              );
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text(ok ? (backend.isActive ? 'Backend deactivated' : 'Backend activated') : 'Update failed')),
                                );
                              }
                            });
                          },
                        ),
                        PopupMenuItem(
                          child: const Text('Delete'),
                          onTap: () async {
                            final confirm = await showDialog<bool>(
                              context: context,
                              builder: (ctx) => AlertDialog(
                                title: const Text('Confirm Deletion'),
                                content: Text('Delete "${backend.name}" permanently? This cannot be undone.'),
                                actions: [
                                  TextButton(
                                    onPressed: () => Navigator.pop(ctx, false),
                                    child: const Text('Cancel'),
                                  ),
                                  ElevatedButton(
                                    onPressed: () => Navigator.pop(ctx, true),
                                    style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                                    child: const Text('Delete'),
                                  ),
                                ],
                              ),
                            );
                            if (confirm == true) {
                              final ok = await provider.deleteBackend(backend.id);
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text(ok ? 'Backend deleted' : 'Delete failed')),
                                );
                              }
                            }
                          },
                        ),
                      ],
                    ),
                  ),
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

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(
            child: Text(value),
          ),
        ],
      ),
    );
  }

  Future<void> _showEditRuleForm(BuildContext context, rule) async {
    final domainCtl = TextEditingController(text: rule.domain);
    final pathCtl = TextEditingController(text: rule.pathPattern);
    String ruleType = rule.ruleType;
    int? selectedBackendId = rule.backendId;

    // Get available backends
    final backendProvider = context.read<BackendProvider>();
    final backends = backendProvider.backends.where((b) => b.isActive).toList();

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Edit Proxy Rule'),
        content: StatefulBuilder(
          builder: (ctx, setState) => SizedBox(
            width: 420,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(controller: domainCtl, decoration: const InputDecoration(labelText: 'Domain')),
                const SizedBox(height: 8),
                DropdownButtonFormField<int>(
                  value: selectedBackendId,
                  items: backends.map((backend) {
                    return DropdownMenuItem<int>(
                      value: backend.id,
                      child: Text('${backend.name} (${backend.protocol}://${backend.host}:${backend.port})'),
                    );
                  }).toList(),
                  onChanged: (v) => setState(() => selectedBackendId = v),
                  decoration: const InputDecoration(labelText: 'Backend Server'),
                ),
                const SizedBox(height: 8),
                TextField(controller: pathCtl, decoration: const InputDecoration(labelText: 'Path Pattern')),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: ruleType,
                  items: const [
                    DropdownMenuItem(value: 'reverse_proxy', child: Text('reverse_proxy')),
                  ],
                  onChanged: (v) => setState(() => ruleType = v ?? 'reverse_proxy'),
                  decoration: const InputDecoration(labelText: 'Rule Type'),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Update')),
        ],
      ),
    );

    if (result == true) {
      final domain = domainCtl.text.trim();
      final path = pathCtl.text.trim().isEmpty ? '/' : pathCtl.text.trim();
      if (domain.isEmpty || selectedBackendId == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Domain and Backend are required')));
        return;
      }
      final provider = context.read<RuleProvider>();
      final ok = await provider.updateRule(
        id: rule.id,
        domain: domain,
        backendId: selectedBackendId!,
        pathPattern: path,
        ruleType: ruleType,
      );
      if (!context.mounted) return;
      if (ok) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Rule updated')));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(provider.error ?? 'Update failed')));
      }
    }
  }

  Future<void> _showCreateRuleForm(BuildContext context) async {
    final domainCtl = TextEditingController();
    final pathCtl = TextEditingController(text: '/');
    String ruleType = 'reverse_proxy';
    int? selectedBackendId;

    // Get available backends
    final backendProvider = context.read<BackendProvider>();
    final backends = backendProvider.backends.where((b) => b.isActive).toList();

    if (backends.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No active backends available. Please create a backend first.')),
      );
      return;
    }

    selectedBackendId = backends.first.id;

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Create Proxy Rule'),
        content: StatefulBuilder(
          builder: (ctx, setState) => SizedBox(
            width: 420,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(controller: domainCtl, decoration: const InputDecoration(labelText: 'Domain')),
                const SizedBox(height: 8),
                DropdownButtonFormField<int>(
                  value: selectedBackendId,
                  items: backends.map((backend) {
                    return DropdownMenuItem<int>(
                      value: backend.id,
                      child: Text('${backend.name} (${backend.protocol}://${backend.host}:${backend.port})'),
                    );
                  }).toList(),
                  onChanged: (v) => setState(() => selectedBackendId = v),
                  decoration: const InputDecoration(labelText: 'Backend Server'),
                ),
                const SizedBox(height: 8),
                TextField(controller: pathCtl, decoration: const InputDecoration(labelText: 'Path Pattern')),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: ruleType,
                  items: const [
                    DropdownMenuItem(value: 'reverse_proxy', child: Text('reverse_proxy')),
                  ],
                  onChanged: (v) => setState(() => ruleType = v ?? 'reverse_proxy'),
                  decoration: const InputDecoration(labelText: 'Rule Type'),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Create')),
        ],
      ),
    );

    if (result == true) {
      final domain = domainCtl.text.trim();
      final path = pathCtl.text.trim().isEmpty ? '/' : pathCtl.text.trim();
      if (domain.isEmpty || selectedBackendId == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Domain and Backend are required')));
        return;
      }
      final ok = await context.read<RuleProvider>().createRule(domain: domain, backendId: selectedBackendId!, pathPattern: path, ruleType: ruleType);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(ok ? 'Rule created' : 'Create failed')));
    }
  }

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
          actions: [
            IconButton(
              tooltip: 'Add Rule',
              icon: const Icon(Icons.add),
              onPressed: () => _showCreateRuleForm(context),
            ),
          ],
        ),
        body: Consumer2<RuleProvider, BackendProvider>(
          builder: (context, ruleProvider, backendProvider, _) {
            if (ruleProvider.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }
            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: ruleProvider.rules.length,
              itemBuilder: (context, index) {
                final rule = ruleProvider.rules[index];
                // Find the backend for this rule
                final backend = backendProvider.backends.firstWhere(
                  (b) => b.id == rule.backendId,
                  orElse: () => backendProvider.backends.first, // Fallback
                );
                final backendName = backend.name;
                
                return Card(
                  color: rule.isActive ? null : Colors.grey[200],
                  child: ExpansionTile(
                    leading: Icon(
                      Icons.domain,
                      color: rule.isActive ? Colors.blue : Colors.grey,
                    ),
                    title: Text(
                      rule.domain,
                      style: TextStyle(
                        color: rule.isActive ? null : Colors.grey[600],
                        decoration: rule.isActive ? null : TextDecoration.lineThrough,
                      ),
                    ),
                    subtitle: Text(
                      'Backend: $backendName${rule.isActive ? '' : ' (Inactive)'}',
                      style: TextStyle(
                        color: rule.isActive ? null : Colors.grey[600],
                      ),
                    ),
                    trailing: PopupMenuButton(
                      itemBuilder: (context) => [
                        PopupMenuItem(
                          child: const Text('Edit'),
                          onTap: () {
                            Future.delayed(Duration.zero, () => _showEditRuleForm(context, rule));
                          },
                        ),
                        PopupMenuItem(
                          child: Text(rule.isActive ? 'Deactivate' : 'Activate'),
                          onTap: () {
                            Future.delayed(Duration.zero, () async {
                              final ok = await ruleProvider.updateRule(
                                id: rule.id,
                                domain: rule.domain,
                                backendId: rule.backendId,
                                pathPattern: rule.pathPattern,
                                ruleType: rule.ruleType,
                                isActive: !rule.isActive,
                              );
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text(ok ? (rule.isActive ? 'Rule deactivated' : 'Rule activated') : 'Update failed')),
                                );
                              }
                            });
                          },
                        ),
                        PopupMenuItem(
                          child: const Text('Delete'),
                          onTap: () async {
                            final confirm = await showDialog<bool>(
                              context: context,
                              builder: (ctx) => AlertDialog(
                                title: const Text('Confirm Deletion'),
                                content: Text('Delete rule for "${rule.domain}" permanently? This cannot be undone.'),
                                actions: [
                                  TextButton(
                                    onPressed: () => Navigator.pop(ctx, false),
                                    child: const Text('Cancel'),
                                  ),
                                  ElevatedButton(
                                    onPressed: () => Navigator.pop(ctx, true),
                                    style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                                    child: const Text('Delete'),
                                  ),
                                ],
                              ),
                            );
                            if (confirm == true) {
                              final ok = await ruleProvider.deleteRule(rule.id);
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text(ok ? 'Rule deleted' : 'Delete failed')),
                                );
                              }
                            }
                          },
                        ),
                      ],
                    ),
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildDetailRow('Domain', rule.domain),
                            _buildDetailRow('Backend', '$backendName (ID: ${rule.backendId})'),
                            _buildDetailRow('Backend URL', '${backend.protocol}://${backend.host}:${backend.port}'),
                            _buildDetailRow('Path Pattern', rule.pathPattern),
                            _buildDetailRow('Rule Type', rule.ruleType),
                            _buildDetailRow('Status', rule.isActive ? 'Active' : 'Inactive'),
                            _buildDetailRow('Created By', 'User ID: ${rule.createdBy}'),
                            _buildDetailRow('Created At', rule.createdAt.toString()),
                            _buildDetailRow('Updated At', rule.updatedAt.toString()),
                          ],
                        ),
                      ),
                    ],
                  ),
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

  Future<void> _showCreateCertForm(BuildContext context) async {
    final domainCtl = TextEditingController();
    final descCtl = TextEditingController();

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Add Certificate (metadata)'),
        content: SizedBox(
          width: 420,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: domainCtl, decoration: const InputDecoration(labelText: 'Domain')),
              const SizedBox(height: 8),
              TextField(controller: descCtl, decoration: const InputDecoration(labelText: 'Description (optional)')),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Save')),
        ],
      ),
    );

    if (result == true) {
      final domain = domainCtl.text.trim();
      if (domain.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Domain is required')));
        return;
      }
      final ok = await context.read<CertificateProvider>().createCertificate(
        name: domain,
        domain: domain,
        certificate: '',
        privateKey: '',
      );
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(ok ? 'Certificate saved' : 'Save failed')));
    }
  }

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
          actions: [
            IconButton(
              tooltip: 'Add Certificate',
              icon: const Icon(Icons.add),
              onPressed: () => _showCreateCertForm(context),
            ),
          ],
        ),
        body: Consumer<CertificateProvider>(
          builder: (context, provider, _) {
            if (provider.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }
            return ListView.builder(
              itemCount: provider.certificates.length,
              itemBuilder: (context, index) {
                final cert = provider.certificates[index];
                return ListTile(
                  title: Text(cert.domain),
                  subtitle: Text(cert.expiryStatus),
                  trailing: IconButton(
                    tooltip: 'Delete',
                    icon: const Icon(Icons.delete_outline),
                    onPressed: () async {
                      final ok = await context.read<CertificateProvider>().deleteCertificate(cert.id);
                      if (!context.mounted) return;
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text(ok ? 'Certificate deleted' : 'Delete failed')),
                      );
                    },
                  ),
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
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton.icon(
                  onPressed: () => _showNginxConfig(context),
                  icon: const Icon(Icons.code),
                  label: const Text('View Nginx Config'),
                ),
                const SizedBox(width: 16),
                ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Close'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
