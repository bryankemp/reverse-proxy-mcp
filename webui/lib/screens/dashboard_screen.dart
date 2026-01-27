import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/backend_provider.dart';
import '../providers/other_providers.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    context.read<BackendProvider>().fetchBackends();
    context.read<RuleProvider>().fetchRules();
    context.read<CertificateProvider>().fetchCertificates();
    context.read<MetricsProvider>().fetchMetrics();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await context.read<AuthProvider>().logout();
              if (context.mounted) {
                Navigator.pushReplacementNamed(context, '/login');
              }
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Consumer<AuthProvider>(
                builder: (_, auth, __) => Text(
                  'Welcome, ${auth.currentUser?.username ?? 'User'}',
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  _StatCard(
                    title: 'Backends',
                    builder: (context) {
                      final count = context
                          .watch<BackendProvider>()
                          .backends
                          .length;
                      return Text(
                        '$count',
                        style: const TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                        ),
                      );
                    },
                  ),
                  const SizedBox(width: 16),
                  _StatCard(
                    title: 'Rules',
                    builder: (context) {
                      final count = context.watch<RuleProvider>().rules.length;
                      return Text(
                        '$count',
                        style: const TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                        ),
                      );
                    },
                  ),
                  const SizedBox(width: 16),
                  _StatCard(
                    title: 'Certificates',
                    builder: (context) {
                      final certs = context
                          .watch<CertificateProvider>()
                          .certificates;
                      final expiring = certs
                          .where((c) => c.expiringInDays < 30)
                          .length;
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${certs.length}',
                            style: const TextStyle(
                              fontSize: 32,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            '$expiring expiring',
                            style: const TextStyle(
                              fontSize: 12,
                              color: Colors.orange,
                            ),
                          ),
                        ],
                      );
                    },
                  ),
                ],
              ),
              const SizedBox(height: 24),
              const Text(
                'Metrics',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              Consumer<MetricsProvider>(
                builder: (_, metrics, __) => Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey.shade300),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _MetricRow(
                        label: 'Total Requests',
                        value: '${metrics.getTotalRequests()}',
                      ),
                      _MetricRow(
                        label: 'Avg Response Time',
                        value:
                            '${metrics.getAverageResponseTime().toStringAsFixed(2)}ms',
                      ),
                      _MetricRow(
                        label: 'Total Errors',
                        value: '${metrics.getTotalErrors()}',
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Consumer<AuthProvider>(
                builder: (_, auth, __) {
                  if (!auth.isAdmin) return const SizedBox.shrink();
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Admin Actions',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: () =>
                              context.read<RuleProvider>().reloadNginx(),
                          icon: const Icon(Icons.refresh),
                          label: const Text('Reload Nginx'),
                        ),
                      ),
                    ],
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final Widget Function(BuildContext) builder;

  const _StatCard({required this.title, required this.builder});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.shade300),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(fontSize: 14, color: Colors.grey),
            ),
            const SizedBox(height: 8),
            builder(context),
          ],
        ),
      ),
    );
  }
}

class _MetricRow extends StatelessWidget {
  final String label;
  final String value;

  const _MetricRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
