import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/other_providers.dart';
import '../models/models.dart';
import '../widgets/app_drawer.dart';

class RulesScreen extends StatefulWidget {
  const RulesScreen({Key? key}) : super(key: key);

  @override
  State<RulesScreen> createState() => _RulesScreenState();
}

class _RulesScreenState extends State<RulesScreen> {
  late TextEditingController _domainController;
  late TextEditingController _backendIdController;

  @override
  void initState() {
    super.initState();
    _domainController = TextEditingController();
    _backendIdController = TextEditingController();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<RuleProvider>().fetchRules();
    });
  }

  @override
  void dispose() {
    _domainController.dispose();
    _backendIdController.dispose();
    super.dispose();
  }

  void _showCreateDialog() {
    _domainController.clear();
    _backendIdController.clear();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Proxy Rule'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _domainController,
                decoration: const InputDecoration(
                  labelText: 'Domain',
                  hintText: 'e.g., example.com',
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _backendIdController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Backend ID',
                  hintText: 'e.g., 1',
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final backendIdText = _backendIdController.text.trim();
              if (_domainController.text.trim().isEmpty ||
                  backendIdText.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Please fill in all fields')),
                );
                return;
              }
              await context.read<RuleProvider>().createRule(
                domain: _domainController.text.trim(),
                backendId: int.parse(backendIdText),
              );
              if (mounted) Navigator.pop(context);
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }

  void _showEditDialog(ProxyRule rule) {
    _domainController.text = rule.domain;
    _backendIdController.text = rule.backendId.toString();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit Proxy Rule'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _domainController,
                decoration: const InputDecoration(labelText: 'Domain'),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _backendIdController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Backend ID'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final backendIdText = _backendIdController.text.trim();
              if (_domainController.text.trim().isEmpty ||
                  backendIdText.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Please fill in all fields')),
                );
                return;
              }
              await context.read<RuleProvider>().updateRule(
                id: rule.id,
                domain: _domainController.text.trim(),
                backendId: int.parse(backendIdText),
              );
              if (mounted) Navigator.pop(context);
            },
            child: const Text('Update'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Proxy Rules'),
        elevation: 0,
        actions: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Center(
              child: Consumer<RuleProvider>(
                builder: (context, provider, _) {
                  return ElevatedButton.icon(
                    onPressed: provider.isReloading
                        ? null
                        : () => provider.reloadNginx(),
                    icon: provider.isReloading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.refresh),
                    label: const Text('Reload Nginx'),
                  );
                },
              ),
            ),
          ),
        ],
      ),
      drawer: const AppDrawer(),
      body: Consumer<RuleProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 64, color: Colors.red),
                  const SizedBox(height: 16),
                  Text(provider.error!),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => provider.fetchRules(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          if (provider.rules.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.domain, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text(
                    'No proxy rules yet',
                    style: TextStyle(fontSize: 18, color: Colors.grey),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _showCreateDialog,
                    icon: const Icon(Icons.add),
                    label: const Text('Add Rule'),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: provider.rules.length,
            itemBuilder: (context, index) {
              final rule = provider.rules[index];
              return Card(
                child: ListTile(
                  title: Text(rule.domain),
                  subtitle: Text('Backend ${rule.backendId}'),
                  trailing: PopupMenuButton(
                    itemBuilder: (context) => [
                      PopupMenuItem(
                        child: const Text('Edit'),
                        onTap: () => _showEditDialog(rule),
                      ),
                      PopupMenuItem(
                        child: Text(rule.isActive ? 'Disable' : 'Enable'),
                        onTap: () => provider.updateRule(
                          id: rule.id,
                          domain: rule.domain,
                          backendId: rule.backendId,
                        ),
                      ),
                      PopupMenuItem(
                        child: const Text('Delete'),
                        onTap: () => provider.deleteRule(rule.id),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showCreateDialog,
        tooltip: 'Add Rule',
        child: const Icon(Icons.add),
      ),
    );
  }
}
