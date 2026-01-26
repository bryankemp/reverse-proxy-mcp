import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/backend_provider.dart';
import '../models/models.dart';
import '../widgets/app_drawer.dart';

class BackendsScreen extends StatefulWidget {
  const BackendsScreen({Key? key}) : super(key: key);

  @override
  State<BackendsScreen> createState() => _BackendsScreenState();
}

class _BackendsScreenState extends State<BackendsScreen> {
  late TextEditingController _nameController;
  late TextEditingController _hostController;
  late TextEditingController _portController;
  late TextEditingController _descriptionController;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController();
    _hostController = TextEditingController();
    _portController = TextEditingController();
    _descriptionController = TextEditingController();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<BackendProvider>().fetchBackends();
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _hostController.dispose();
    _portController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  void _showCreateDialog() {
    _nameController.clear();
    _hostController.clear();
    _portController.text = '80';
    _descriptionController.clear();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Backend Server'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Server Name',
                  hintText: 'e.g., Web Server 1',
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _hostController,
                decoration: const InputDecoration(
                  labelText: 'Hostname or IP',
                  hintText: 'e.g., 192.168.1.10',
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _portController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Port',
                  hintText: 'e.g., 80',
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _descriptionController,
                decoration: const InputDecoration(
                  labelText: 'Description',
                  hintText: 'Optional notes',
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
              await context.read<BackendProvider>().createBackend(
                name: _nameController.text,
                host: _hostController.text,
                port: int.parse(_portController.text),
                description: _descriptionController.text,
              );
              if (mounted) Navigator.pop(context);
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }

  void _showEditDialog(BackendServer backend) {
    _nameController.text = backend.name;
    _hostController.text = backend.host;
    _portController.text = backend.port.toString();
    _descriptionController.text = backend.description ?? '';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit Backend Server'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _nameController,
                decoration: const InputDecoration(labelText: 'Server Name'),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _hostController,
                decoration: const InputDecoration(labelText: 'Hostname or IP'),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _portController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Port'),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _descriptionController,
                decoration: const InputDecoration(labelText: 'Description'),
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
              await context.read<BackendProvider>().updateBackend(
                id: backend.id,
                name: _nameController.text,
                host: _hostController.text,
                port: int.parse(_portController.text),
                description: _descriptionController.text,
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
      appBar: AppBar(title: const Text('Backend Servers'), elevation: 0),
      drawer: const AppDrawer(),
      body: Consumer<BackendProvider>(
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
                    onPressed: () => provider.fetchBackends(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          if (provider.backends.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.storage, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text(
                    'No backend servers yet',
                    style: TextStyle(fontSize: 18, color: Colors.grey),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _showCreateDialog,
                    icon: const Icon(Icons.add),
                    label: const Text('Add Backend'),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
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
                      decoration: backend.isActive
                          ? null
                          : TextDecoration.lineThrough,
                    ),
                  ),
                  subtitle: Text(
                    '${backend.host}:${backend.port}${backend.isActive ? '' : ' (Inactive)'}',
                    style: TextStyle(
                      color: backend.isActive ? null : Colors.grey[600],
                    ),
                  ),
                  trailing: PopupMenuButton(
                    itemBuilder: (context) => [
                      PopupMenuItem(
                        child: const Text('Edit'),
                        onTap: () => _showEditDialog(backend),
                      ),
                      PopupMenuItem(
                        child: Text(
                          backend.isActive ? 'Deactivate' : 'Activate',
                        ),
                        onTap: () => provider.updateBackend(
                          id: backend.id,
                          name: backend.name,
                          host: backend.host,
                          port: backend.port,
                          isActive: !backend.isActive,
                        ),
                      ),
                      PopupMenuItem(
                        child: const Text('Delete'),
                        onTap: () async {
                          // Show confirmation dialog
                          final confirm = await showDialog<bool>(
                            context: context,
                            builder: (ctx) => AlertDialog(
                              title: const Text('Confirm Deletion'),
                              content: Text(
                                'Delete "${backend.name}" permanently? This cannot be undone.',
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
                            await provider.deleteBackend(backend.id);
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
        tooltip: 'Add Backend',
        child: const Icon(Icons.add),
      ),
    );
  }
}
