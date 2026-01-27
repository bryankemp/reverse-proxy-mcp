import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import '../providers/other_providers.dart';
import '../models/models.dart';
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
  String? _certFileName;
  String? _keyFileName;
  bool _isDefault = false;

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

  Future<void> _pickCertFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['crt', 'pem', 'cer', 'cert'],
        withData: true,
      );

      if (result != null && result.files.single.bytes != null) {
        final bytes = result.files.single.bytes!;
        final content = String.fromCharCodes(bytes);
        setState(() {
          _certController.text = content;
          _certFileName = result.files.single.name;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error picking certificate file: $e')),
        );
      }
    }
  }

  Future<void> _pickKeyFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['key', 'pem'],
        withData: true,
      );

      if (result != null && result.files.single.bytes != null) {
        final bytes = result.files.single.bytes!;
        final content = String.fromCharCodes(bytes);
        setState(() {
          _keyController.text = content;
          _keyFileName = result.files.single.name;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error picking key file: $e')),
        );
      }
    }
  }

  void _showCreateDialog() {
    _nameController.clear();
    _domainController.clear();
    _certController.clear();
    _keyController.clear();
    _certFileName = null;
    _keyFileName = null;
    _isDefault = false;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Certificate'),
        content: StatefulBuilder(
          builder: (ctx, setLocalState) => SingleChildScrollView(
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
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _certController,
                      maxLines: 3,
                      decoration: InputDecoration(
                        labelText: 'Certificate',
                        hintText: _certFileName ?? '-----BEGIN CERTIFICATE-----',
                      ),
                      readOnly: true,
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton.icon(
                    onPressed: _pickCertFile,
                    icon: const Icon(Icons.file_upload),
                    label: const Text('Pick File'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _keyController,
                      maxLines: 3,
                      decoration: InputDecoration(
                        labelText: 'Private Key',
                        hintText: _keyFileName ?? '-----BEGIN PRIVATE KEY-----',
                      ),
                      readOnly: true,
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton.icon(
                    onPressed: _pickKeyFile,
                    icon: const Icon(Icons.file_upload),
                    label: const Text('Pick File'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              CheckboxListTile(
                title: const Text('Set as Default Certificate'),
                value: _isDefault,
                onChanged: (value) {
                  setLocalState(() {
                    _isDefault = value ?? false;
                  });
                },
                controlAffinity: ListTileControlAffinity.leading,
              ),
            ],
          ),
        ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final ok = await context.read<CertificateProvider>().createCertificate(
                name: _nameController.text.trim(),
                domain: _domainController.text.trim(),
                certificate: _certController.text,
                privateKey: _keyController.text,
                isDefault: _isDefault,
                certFileName: _certFileName,
                keyFileName: _keyFileName,
              );
              if (ok && mounted) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Certificate added')),
                );
              }
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }

  String _getExpiryStatus(DateTime expiryDate) {
    final now = DateTime.now().toUtc();
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
      appBar: AppBar(title: const Text('SSL Certificates'), elevation: 0),
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
              final isExpiring =
                  cert.expiryDate.difference(DateTime.now().toUtc()).inDays < 30;

              return Card(
                child: ListTile(
                  leading: Icon(
                    cert.isDefault ? Icons.star : Icons.security,
                    color: cert.isDefault ? Colors.amber : Colors.blue,
                  ),
                  title: Row(
                    children: [
                      Text(cert.name),
                      if (cert.isDefault) ...[
                        const SizedBox(width: 8),
                        const Chip(
                          label: Text(
                            'DEFAULT',
                            style: TextStyle(fontSize: 10),
                          ),
                          backgroundColor: Colors.amber,
                          padding: EdgeInsets.symmetric(horizontal: 4),
                        ),
                      ],
                    ],
                  ),
                  subtitle: Text(
                    '$expiryStatus • ${cert.domain}',
                    style: TextStyle(
                      color: isExpiring ? Colors.orange : Colors.grey[600],
                    ),
                  ),
                  trailing: PopupMenuButton(
                    itemBuilder: (context) => [
                      if (!cert.isDefault)
                        PopupMenuItem(
                          child: const Text('Set as Default'),
                          onTap: () async {
                            final success = await provider
                                .setDefaultCertificate(cert.id);
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                    success
                                        ? 'Certificate set as default'
                                        : provider.error ??
                                              'Failed to set default',
                                  ),
                                ),
                              );
                            }
                          },
                        ),
                      PopupMenuItem(
                        child: const Text('Delete'),
                        onTap: () async {
                          final confirm = await showDialog<bool>(
                            context: context,
                            builder: (ctx) => AlertDialog(
                              title: const Text('Confirm Deletion'),
                              content: Text(
                                'Delete certificate "${cert.name}" permanently? This cannot be undone.',
                              ),
                              actions: [
                                TextButton(
                                  onPressed: () => Navigator.pop(ctx, false),
                                  child: const Text('Cancel'),
                                ),
                                ElevatedButton(
                                  onPressed: () => Navigator.pop(ctx, true),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.red,
                                  ),
                                  child: const Text('Delete'),
                                ),
                              ],
                            ),
                          );
                          if (confirm == true) {
                            await provider.deleteCertificate(cert.id);
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
      floatingActionButton: FloatingActionButton(
        onPressed: _showCreateDialog,
        tooltip: 'Add Certificate',
        child: const Icon(Icons.add),
      ),
    );
  }
}
