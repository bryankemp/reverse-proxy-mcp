import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/certificate_provider.dart';
import '../models/certificate.dart';
import '../widgets/app_drawer.dart';

class CertificatesScreen extends StatefulWidget {
  const CertificatesScreen({Key? key}) : super(key: key);

  @override
  State<CertificatesScreen> createState() => _CertificatesScreenState();
}

class _CertificatesScreenState extends State<CertificatesScreen> {
  late TextEditingController _nameController;
  late TextEditingController _domainController;
  late TextEditingController _certController;
  late TextEditingController _keyController;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController();
    _domainController = TextEditingController();
    _certController = TextEditingController();
    _keyController = TextEditingController();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<CertificateProvider>().fetchCertificates();
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _domainController.dispose();
    _certController.dispose();
    _keyController.dispose();
    super.dispose();
  }

  void _showCreateDialog() {
    _nameController.clear();
    _domainController.clear();
    _certController.clear();
    _keyController.clear();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Certificate'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Certificate Name',
                  hintText: 'e.g., example.com SSL',
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _domainController,
                decoration: const InputDecoration(
                  labelText: 'Domain',
                  hintText: 'e.g., example.com',
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _certController,
                maxLines: 5,
                decoration: const InputDecoration(
                  labelText: 'Certificate',
                  hintText: '-----BEGIN CERTIFICATE-----',
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _keyController,
                maxLines: 5,
                decoration: const InputDecoration(
                  labelText: 'Private Key',
                  hintText: '-----BEGIN PRIVATE KEY-----',
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
              await context.read<CertificateProvider>().createCertificate(
                    name: _nameController.text,
                    domain: _domainController.text,
                    certificate: _certController.text,
                    privateKey: _keyController.text,
                  );
              if (mounted) Navigator.pop(context);
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }

  String _getExpiryStatus(DateTime expiryDate) {
    final now = DateTime.now();
    final daysUntilExpiry = expiryDate.difference(now).inDays;

    if (daysUntilExpiry < 0) {
      return 'Expired';
    } else if (daysUntilExpiry < 30) {
      return 'Expiring soon ($daysUntilExpiry days)';
    } else {
      return 'Valid ($daysUntilExpiry days)';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SSL Certificates'),
        elevation: 0,
      ),
      drawer: const AppDrawer(),
      body: Consumer<CertificateProvider>(
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
                    onPressed: () => provider.fetchCertificates(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          if (provider.certificates.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.security, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text(
                    'No certificates yet',
                    style: TextStyle(fontSize: 18, color: Colors.grey),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _showCreateDialog,
                    icon: const Icon(Icons.add),
                    label: const Text('Add Certificate'),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: provider.certificates.length,
            itemBuilder: (context, index) {
              final cert = provider.certificates[index];
              final expiryStatus = _getExpiryStatus(cert.expiryDate);
              final isExpiring = cert.expiryDate.difference(DateTime.now()).inDays < 30;

              return Card(
                child: ListTile(
                  title: Text(cert.name),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Domain: ${cert.domain}'),
                      Text(
                        expiryStatus,
                        style: TextStyle(
                          color: isExpiring ? Colors.orange : Colors.green,
                        ),
                      ),
                    ],
                  ),
                  trailing: PopupMenuButton(
                    itemBuilder: (context) => [
                      PopupMenuItem(
                        child: const Text('Delete'),
                        onTap: () =>
                            provider.deleteCertificate(cert.id),
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
        tooltip: 'Add Certificate',
        child: const Icon(Icons.add),
      ),
    );
  }
}
